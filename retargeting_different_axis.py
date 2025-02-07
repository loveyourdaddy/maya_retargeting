# Adori Asooni Metahuman UE
# mayapy retargeting_different_axis.py --sourceChar "./models/Asooni/Asooni.fbx" --sourceMotion "./motions/Asooni/Super shy - New Jeans_RT1226.fbx" --targetChar "./models/Adori/Adori.fbx"
# mayapy retargeting_different_axis.py --sourceChar "./models/Adori/Adori.fbx" --sourceMotion "./motions/Adori/Nonsense_RT0227.fbx" --targetChar "./models/Asooni/Asooni.fbx"

''' 
Naming
원본 이름 
tgt_joints_real_origin

namespace 수정됨
tgt_joints_wNS: 원본 hierarchy, 네임스페이스만 바뀐것. 
tgt_joints_template: 원본 Hier, template joint만 renamed된것
tgt_joints_common: Hierarchy가 바뀐것.
'''

import maya.cmds as cmds
import maya.standalone
from functions.parser import *
from functions.character import *
from functions.motion import *
from functions.maya import *
from functions.retarget import *
import time

def main():
    start_time = time.time()
    maya.standalone.initialize(name='python')

    # Load the FBX plugin
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        cmds.loadPlugin('fbxmaya')
    
    # name
    args = get_args()
    # tgt
    targetChar = get_name(args.targetChar)
    targetMotion = get_name(args.sourceMotion)
    # src
    sourceMotion = args.sourceMotion
    sourceChar = sourceMotion.split('/')[-2]
    print(">> Source: ({}, {}) -> Target: {}".format(sourceChar, sourceMotion, targetChar))


    ''' Target '''
    # character
    mel.eval('FBXImportSmoothingGroups -v true')
    mel.eval('FBXImport -f"{}"'.format(args.targetChar))
    # .fbm 폴더 경로
    path = "./models/" + targetChar + "/" + targetChar
    fbm_folder = path + ".fbm"
    
    # import texture
    # 모든 파일 노드 가져오기
    file_nodes = cmds.ls(type="file")
    for node in file_nodes:
        # 현재 파일 경로 가져오기
        new_path = os.path.join(fbm_folder, node)
        
        # 새 경로가 존재하는지 확인
        if os.path.exists(new_path):
            # 텍스처 경로 업데이트
            cmds.setAttr(node + ".fileTextureName", new_path, type="string")
            # print(f">>Texture loaded: {node} -> {new_path}")
        else:
            print(f">>No texture: {new_path}")

    # joints
    tgt_joints_wNS, tgt_joints_origin_woNS, tgt_chain_index, tgt_root_joints = get_tgt_joints()
    
    # locator list
    tgt_locator_list = []
    tgt_joints_list = []
    tgt_parent_node_list = []
    for root_id, root in enumerate(tgt_root_joints):
        # update root 
        root = "tgt:" + root.split(":")[-1]
        
        # joints
        tgt_joints = get_joint_hierarchy(root)
        tgt_joints_list.append(tgt_joints)
        
        # locator 
        locator = cmds.listRelatives(root, parent=True, shapes=True)[-1]
        tgt_locator_list.append(locator)
        tgt_locator_list.append(locator+'Shape')

        parent_node = cmds.listRelatives(root, parent=True, shapes=True)[-1]
        tgt_parent_node_list.append(parent_node)

    # 다른 locator가 있다면 추가해주기
    additional_locators_list = cmds.ls(type='locator')
    for additional_loctor in additional_locators_list:
        if additional_loctor not in tgt_locator_list:
            tgt_locator_list.append(additional_loctor)
            tgt_locator_list.append(additional_loctor+'Shape')
    
    # 타겟 조인트를 selected chain으로 변경
    parent_node = tgt_parent_node_list[tgt_chain_index]
    tgt_joints_wNS = tgt_joints_list[tgt_chain_index]
    
    # joint templated
    tgt_joints_template, _, tgt_joints_template_indices = rename_joint_by_template(tgt_joints_wNS)

    # sub chain
    # 다른 chaing에 대해서 main skeleton을 찾기
    tgt_subchains = []
    tgt_subchain_template = []
    tgt_subchain_template_indices = []
    for cid, joints in enumerate(tgt_joints_list):
        if cid==tgt_chain_index:
            continue
        tgt_subchains.append(joints)
        
        # index 
        chain_joints_template, _, template_indices = rename_joint_by_template(joints)
        tgt_subchain_template.append(chain_joints_template)
        tgt_subchain_template_indices.append(template_indices)

    # subchain root
    subchain_roots = []
    subchain_template_roots = []
    for j, subchain in enumerate(tgt_subchains):
        subchain_roots.append(subchain[0])
        subchain_template_roots.append(tgt_subchain_template[j][0])
    
    # locator
    if parent_node is not None:
        tgt_locator, tgt_locator_angle, tgt_locator_scale, tgt_locator_pos = get_locator(parent_node)
        # add namespace
        tgt_locator = "tgt:" + tgt_locator
    else:
        tgt_locator = None

    # rename locator
    tgt_locator_list = add_namespace_for_joints(tgt_locator_list, "tgt")
    
    # meshes
    tgt_meshes = cmds.ls(type='mesh')
    tgt_meshes = add_namespace_for_meshes(tgt_meshes, "tgt_mesh")


    ''' Source char '''
    sourceChar_path = './models/' + sourceChar + '/' + sourceChar + '.fbx'

    # import source character
    if os.path.exists(sourceChar_path)==False:
        # source character가 없을때, 0 frame을 Tpose로 사용.
        print(">> no source character")
        raise ValueError("No source character")
    
    mel.eval('FBXImport -f"{}"'.format(sourceChar_path))
    src_joints_origin = get_src_joints(tgt_joints_wNS)
    src_joints_template, _, _ = rename_joint_by_template(src_joints_origin)

    # locator
    locators_list = cmds.ls(type='locator')
    src_locator_list = list(set(locators_list) - set(tgt_locator_list))
    if len(src_locator_list)!=0:
        # Select right locator
        src_locator_list = sorted(src_locator_list, key=lambda x: len(cmds.listRelatives(x, children=True) or []), reverse=True)
        
        # src locator선택: namespace tgt가 없는 경우
        src_locator_candidate = [] 
        for locator in src_locator_list:
            if locator.split(':')[0] != 'tgt':
                src_locator_candidate.append(locator)

        # 가장 많은 자식을 가진 locator를 선택하기 위해 0을 선택
        src_locator = src_locator_candidate[0]

        # Get locator info 
        src_locator, src_locator_angle, src_locator_scale, src_locator_pos = get_locator(src_locator)
    else:
        src_locator = None


    ''' Common skeleton '''
    # common joint 
    src_joints_common, src_Tpose_rots_common, \
    tgt_joints_common, tgt_Tpose_rots_common, tgt_joints_template_indices, \
    conversion_matrics \
        = get_conversion(
            src_joints_origin, src_joints_template, 
            tgt_joints_wNS, tgt_joints_template, tgt_joints_template_indices)

    # for subchain joints 
    subchain_conversion_matrics = []
    tgt_subchain_template_indices_refined = []
    subchain_common_joints = []
    subchain_Tpose_rots_common = []
    for j, subchain_joints in enumerate(tgt_subchains):
        _, _, \
        subchain_joints_common, subchain_Tpose_rots_common, tgt_subchain_template_index, \
        subchain_conversion_matrics \
            = get_conversion(
                src_joints_origin, src_joints_template, 
                subchain_joints, tgt_subchain_template[j], tgt_subchain_template_indices[j], 
                root_joint=subchain_template_roots[j])
        subchain_common_joints.append(subchain_joints_common)
        tgt_subchain_template_indices_refined.append(tgt_subchain_template_index)
        subchain_conversion_matrics.append(subchain_conversion_matrics)
    tgt_subchain_template_indices = tgt_subchain_template_indices_refined
    
    # root
    src_hip_index = get_root_joint(src_joints_common)
    tgt_hip_index = get_root_joint(tgt_joints_common)
    src_root = src_joints_common[src_hip_index]
    tgt_root = tgt_joints_common[tgt_hip_index]
    # hip height
    src_hip_height = get_distance_from_toe_to_root(src_joints_common, src_root)
    tgt_hip_height = get_distance_from_toe_to_root(tgt_joints_common, tgt_root)

    # ratio
    height_ratio = tgt_hip_height / src_hip_height

    # subchain
    # position
    hip_local_pos = np.array(cmds.xform(tgt_root, query=True, translation=True, worldSpace=False))
    # diff vec wo root rotation
    subchain_local_diff_vec = []
    for root in subchain_roots:
        sub_hip_local_pos = np.array(cmds.xform(root, query=True, translation=True, worldSpace=False))
        local_diff_vec = sub_hip_local_pos - hip_local_pos
        subchain_local_diff_vec.append(local_diff_vec)


    ''' Source motion '''
    mel.eval('FBXImport -f"{}"'.format(sourceMotion))

    # Set fps of source motion
    current_fps = mel.eval('currentTimeUnitToFPS')
    mel.eval(f'currentUnit "{current_fps}fps"')
    print("fps: ", current_fps)

    ''' Refine locator rotation '''
    if tgt_locator is not None:
        # locator ~ root 위 조인트 포함
        tgt_locator_angle = update_root_to_locator_rotation(tgt_joints_wNS, tgt_root, tgt_locator_angle)

    # src meshes
    all_meshes = cmds.ls(type='mesh')
    src_meshes = list(set(all_meshes) - set(tgt_meshes))


    ''' Retarget '''
    if src_locator is not None or tgt_locator is not None:
        # 둘 중 하나라도 locator가 있는 경우 
        # 예외처리
        if src_locator is None:
            src_locator_angle, src_locator_scale = None, None
        if tgt_locator is None:
            tgt_locator_angle, tgt_locator_scale = None, None
        
        # Get data
        trans_data, _ = get_keyframe_data(src_root) # trans, rot 
        trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
        trans_data = get_array_from_keyframe_data(trans_data, trans_attr, src_root)
        len_frame = len(trans_data)

        # rot
        tgt_local_angles = retarget_rotation(src_joints_common, src_Tpose_rots_common,
                          tgt_joints_common, tgt_Tpose_rots_common, tgt_joints_template_indices, conversion_matrics, 
                          subchain_common_joints, subchain_Tpose_rots_common, tgt_subchain_template_indices, subchain_conversion_matrics,
                          len_frame)
        
        # trans
        trans_data = retarget_translation(src_root, tgt_root, 
                                          trans_data, tgt_local_angles[:, src_hip_index], tgt_Tpose_rots_common[src_hip_index],
                                          subchain_roots,
                                          src_locator, src_locator_angle, src_locator_scale,
                                          tgt_locator, tgt_locator_angle, tgt_locator_scale, tgt_locator_pos,
                                            height_ratio, subchain_local_diff_vec, 
                                            len_frame)
    else:
        print(">> retarget without locator")
        raise ValueError("No locator") # TODO
    
    ''' export '''
    # Remove source locator
    if src_locator is not None:
        delete_locator_and_hierarchy(src_locator)
    else:
        delete_locator_and_hierarchy(src_joints_common[0])
    
    # meshes
    cmds.delete(src_meshes)

    # rename tgt joint
    for joint in tgt_joints_origin_woNS:
        if len(joint.split(':'))>1:
            # 만약 target name에 namespace가 있다면 
            # change namespace
            namespace = joint.split(':')[:-1][0] + ":"
            joint = joint.split(':')[-1]
            # 만약 조인트가 존재한다면 
            if cmds.objExists('tgt:'+joint):
                cmds.rename('tgt:'+joint, namespace+joint)
        else:
            if cmds.objExists('tgt:'+joint):
                cmds.rename('tgt:'+joint, joint)
    
    # rename tgt locat
    tgt_locator_list = remove_namespace_for_joints(tgt_locator_list)[0]

    # Delete node 
    delete_all_transform_nodes()

    # export
    print(">> Source: ({}, {}) -> Target: {}".format(sourceChar, sourceMotion, targetChar))
    export(args, targetChar, targetMotion)
    
    # end
    maya.standalone.uninitialize()

    # end time
    end_time = time.time()
    execution_time = end_time - start_time
    minutes = int(execution_time // 60)
    seconds = execution_time % 60
    print(f">> Execution time: {execution_time:.3f}, ({minutes}m {seconds:.3f}s)")

if __name__=="__main__":
    main()
