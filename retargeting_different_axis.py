"""
# 3개 입력: sourceChar, sourceMotion, targetChar
mayapy retargeting_different_axis.py --sourceChar "./models/Adori/Adori.fbx" --sourceMotion "./motions/Adori/Supershy.fbx" --targetChar "./models/Asooni/Asooni.fbx"

# 2개 입력: sourceMotion, targetChar 
mayapy retargeting_different_axis.py --sourceMotion "./motions/Adori/Supershy_wMesh.fbx" --targetChar "./models/Asooni/Asooni.fbx"

# bvh 
mayapy retargeting_different_axis.py --sourceChar "./models/SMPL/SMPL.fbx" --sourceMotion "./motions/SMPL/SuperShy.bvh" --targetChar "./models/Asooni/Asooni.fbx" 
mayapy retargeting_different_axis.py --sourceChar "./models/SMPL/SMPL.fbx" --sourceMotion "./motions/SMPL/IAM.bvh" --targetChar "./models/Asooni/Asooni.fbx"
"""

'''
TODO: class화 하기
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
from functions.bvh_parsing import *
from functions.log import *
from make_Tpose import make_Tpose
import time

def import_motion_file(file_path, scale=1.0):
    """Import motion file (FBX or BVH)"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.fbx':
        mel.eval('FBXImport -f"{}"'.format(file_path))
        return 
    elif file_ext == '.bvh':
        grp, fps = import_bvh(file_path, scale=scale)
        return grp, fps
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


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
    # src char 
    if args.sourceChar != '':
        sourceChar = args.sourceChar.split('/')[-2]
    else:
        sourceChar = sourceMotion.split('/')[-2]

    # 로거 설정
    logger = setup_logger(sourceChar, sourceMotion, targetChar)
    logger.info(f"Source: ({sourceChar}, {sourceMotion}) -> Target: {targetChar}")
    

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
    tgt_meshes = add_namespace_for_meshes(tgt_meshes, "tgt")


    ''' Source char '''
    # import source character
    sourceChar_path = './models/' + sourceChar + '/' + sourceChar + '.fbx'
    if os.path.exists(sourceChar_path):
        # source character가 있다면 import 
        mel.eval('FBXImport -f"{}"'.format(sourceChar_path))
    elif os.path.exists(sourceChar_path)==False or args.sourceChar == '':
        # sourceCharacter가 없거나, sourceChar가 입력으로 들어오지 않는다면,  
        if os.path.exists(sourceChar_path)==False:
            print(">> no source character")
        if args.sourceChar == '':
            print(">> source character is not feded")

        # 해당 path의 tpose 가져오기 
        format = sourceMotion.split('.')[-1]
        Tpose_path = os.path.join(os.path.dirname(sourceMotion), 'Tpose.' + format)
        # import_motion_file(Tpose_path, scale=1)

        # import_motion_file(sourceMotion)
        # make_Tpose() # TODO: make Tpose 
    else:
        raise ValueError("no source character") 

    # rename src meshes
    all_meshes = cmds.ls(type='mesh')
    src_meshes = list(set(all_meshes) - set(tgt_meshes))
    # refine src_meshes
    src_meshes = [mesh for mesh in src_meshes if not mesh.startswith('tgt:')]

    # joints 
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


    # ''' Common skeleton '''
    # # common joint 
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
    file_ext = os.path.splitext(sourceMotion)[1].lower()
    current_fps =  None 
    if file_ext == '.fbx':
        import_motion_file(sourceMotion)
    elif file_ext == '.bvh':
        _, current_fps = import_motion_file(sourceMotion)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


    # Set fps of source motion
    if current_fps is None:
        current_fps = mel.eval('currentTimeUnitToFPS')
    mel.eval(f'currentUnit "{current_fps}fps"') 
    print("source fps: ", current_fps)


    ''' Refine locator rotation '''
    if tgt_locator is not None:
        # locator ~ root 위 조인트 포함
        tgt_locator_angle = update_root_to_locator_rotation(tgt_joints_wNS, tgt_root, tgt_locator_angle)


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
    # Remove source TODO: remove src
    # source locator and joints
    if src_locator is not None:
        delete_locator_and_hierarchy(src_locator)
    else:
        delete_locator_and_hierarchy(src_joints_common[0])
    
    # meshes
    # refine src_meshes in cmds.ls(type='mesh')
    for mesh in src_meshes:
        if mesh in cmds.ls(type='mesh'):
            remove_transform_node([mesh])


    # Rename tgt 
    # joint
    for joint in tgt_joints_origin_woNS:
        if len(joint.split(':'))>1:
            # 만약 target name에 namespace가 있다면 change namespace
            namespace = joint.split(':')[:-1][0] + ":"
            joint = joint.split(':')[-1]
            # 만약 조인트가 존재한다면 
            if cmds.objExists('tgt:'+joint):
                cmds.rename('tgt:'+joint, namespace+joint)
        else:
            if cmds.objExists('tgt:'+joint):
                cmds.rename('tgt:'+joint, joint)

    # mesh 
    # 변형 노드 가져오기
    meshes = cmds.ls(type='mesh')
    transforms = []
    for mesh in meshes:
        parent = cmds.listRelatives(mesh, parent=True)
        if parent:
            transforms.append(parent[0])
    # 중복 제거
    transforms = list(set(transforms))  

    # 변형 노드에서 네임스페이스 제거
    new_transforms = remove_namespace_from_objects(transforms)
    
    # rename tgt locat
    tgt_locator_list = remove_namespace_for_joints(tgt_locator_list)[0]


    # export and end
    export(args, targetChar, targetMotion)
    maya.standalone.uninitialize()

    # end time
    end_time = time.time()
    execution_time = end_time - start_time
    minutes = int(execution_time // 60)
    seconds = execution_time % 60
    print(f">> Execution time: {execution_time:.3f}, ({minutes}m {seconds:.3f}s)")
    logger.info(f"Execution time: {execution_time:.3f}, ({minutes}m {seconds:.3f}s)")

if __name__=="__main__":
    main()
