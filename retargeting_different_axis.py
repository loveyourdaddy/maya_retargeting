"""
Usage:
mayapy retargeting_different_axis.py --sourceMotion "" --targetChar ""

example:
mayapy retargeting_different_axis.py --sourceChar "./models/Asooni/Asooni.fbx" --sourceMotion "./motions/Asooni/Super shy - New Jeans_RT1226.fbx" --targetChar "./models/Adori/Adori.fbx"
"""

''' 
Naming
원본 이름 
tgt_joints_real_origin

namespace 수정됨
tgt_joints_origin: 원본 hierarchy, 네임스페이스만 바뀐것. 
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
    print(">> Retargeting start")
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
    print(">>({}, {}) ->  {}".format(sourceChar, sourceMotion, targetChar))


    ''' tgt '''
    # character
    mel.eval('FBXImportSmoothingGroups -v true')
    mel.eval('FBXImport -f"{}"'.format(args.targetChar))
    # .fbm 폴더 경로
    path = "./models/" + targetChar + "/" + targetChar
    fbm_folder = path + ".fbm"
    print("import done")
    
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
            print(f">>Texture loaded: {node} -> {new_path}")
        else:
            print(f">>No texture: {new_path}")

    # joints
    tgt_joints_origin, tgt_joints_original_name, tgt_root_joint, tgt_root_joints = get_tgt_joints()
    parent_node = cmds.listRelatives(tgt_root_joint, parent=True, shapes=True)[-1]

    ''' rename joint '''
    # renamed by template
    tgt_joints_template = rename_joint_by_template(tgt_joints_origin)

    # locator
    if parent_node is not None:
        tgt_locator, tgt_locator_rot, tgt_locator_scale, tgt_locator_pos = get_locator(parent_node)
    else:
        tgt_locator = None
    
    # locator list
    tgt_locator_list = []
    for root_id, root in enumerate(tgt_root_joints):
        locator = cmds.listRelatives(root, parent=True, shapes=True)[-1]
        tgt_locator_list.append(locator)
        tgt_locator_list.append(locator+'Shape')

    # meshes
    tgt_meshes = cmds.ls(type='mesh')
    tgt_meshes = add_namespace_for_meshes(tgt_meshes, "tgt_mesh")
    print(">> tgt loaded")


    ''' src '''
    sourceChar_path = './models/' + sourceChar + '/' + sourceChar + '.fbx'

    # import source character
    if os.path.exists(sourceChar_path)==False:
        # source character가 없을때, 0 frame을 Tpose로 사용.
        print(">> no source character")
        raise ValueError("No source character")
    
    mel.eval('FBXImport -f"{}"'.format(sourceChar_path))
    src_joints_origin = get_src_joints(tgt_joints_origin)

    # src joint template
    src_joints_template = rename_joint_by_template(src_joints_origin)

    ''' common skeleton '''
    src_joints_common, tgt_joints_common, src_indices, tgt_indices, parent_indices\
        = get_common_src_tgt_joint_hierarchy(src_joints_origin, src_joints_template, tgt_joints_origin, tgt_joints_template)

    # Tpose rot common
    tgt_Tpose_rots_common = get_Tpose_localrot(tgt_joints_common)
    src_Tpose_rots_common = get_Tpose_localrot(src_joints_common)

    # prerot
    if tgt_locator is not None:
        prerotations = get_prerotations(tgt_joints_common, tgt_joints_origin, tgt_locator, tgt_locator_rot)
    else:
        prerotations = get_prerotations(tgt_joints_common)

    # Tpose trf
    conversion_matrics = get_conversion_matrix(src_joints_common, tgt_joints_common)

    # import src motion
    mel.eval('FBXImport -f"{}"'.format(sourceMotion))


    ''' Root, height '''
    # root 
    src_hip_index = get_root_joint(src_joints_common)
    tgt_hip_index = get_root_joint(tgt_joints_common)
    # src_joints_common
    src_root = src_joints_common[src_hip_index]
    tgt_root = tgt_joints_common[tgt_hip_index]

    # hip height
    src_hip_height = cmds.xform(src_root, query=True, translation=True, worldSpace=True)[1]
    tgt_hip_height = cmds.xform(tgt_root, query=True, translation=True, worldSpace=True)[1]

    # 만약 hip height가 0이면 발끝부터 root 까지의 거리를 계산
    if src_hip_height < 0.01:
        src_hip_height = get_distance_from_toe_to_root(src_joints_common, src_root)
    if tgt_hip_height < 0.01:
        tgt_hip_height = get_distance_from_toe_to_root(tgt_joints_common, tgt_root)

    # ratio
    height_ratio = tgt_hip_height / src_hip_height

    # locator rotation 업데이트
    if tgt_locator is not None:
        # locator ~ root 위 조인트 포함
        tgt_locator_rot = update_root_to_locator_rotation(tgt_joints_origin, tgt_root, tgt_locator_rot)

    # locator and meshes 
    locators_list = cmds.ls(type='locator')
    src_locator_list = list(set(locators_list) - set(tgt_locator_list))
    if len(src_locator_list)!=0:
        # Select right locator
        src_locator_list = sorted(src_locator_list, key=lambda x: len(cmds.listRelatives(x, children=True) or []), reverse=True)
        #  가장 많은 자식을 가진 locator를 선택하기 위해 0을 선택 
        src_locator = src_locator_list[0]

        # Get locator info 
        src_locator, src_locator_rot, src_locator_scale, src_locator_pos = get_locator(src_locator)
    else:
        src_locator = None

    # src meshes
    all_meshes = cmds.ls(type='mesh')
    src_meshes = list(set(all_meshes) - set(tgt_meshes))


    ''' Retarget '''
    if src_locator is not None or tgt_locator is not None:
        # 둘 중 하나라도 locator가 있는 경우 
        # 예외처리
        if src_locator is None:
            src_locator_rot, src_locator_scale = None, None
        if tgt_locator is None:
            tgt_locator_rot, tgt_locator_scale = None, None
        
        # trans
        trans_data = retarget_translation(src_root, tgt_root,\
                                          src_locator, src_locator_rot, src_locator_scale,\
                                          tgt_locator, tgt_locator_rot, tgt_locator_scale, tgt_locator_pos,\
                                            height_ratio)
        len_frame = len(trans_data)
        # rot
        retarget_rotation(src_joints_common, tgt_joints_common, src_joints_origin, tgt_joints_origin, 
                          conversion_matrics,  
                          src_Tpose_rots_common, tgt_Tpose_rots_common, src_indices, tgt_indices, 
                          len_frame, src_locator_rot, tgt_locator_rot,
                            prerotations)
        
        # if other locator, retarget also
        # tgt_locator_list TODO
    else:
        print(">> retarget without locator")
        raise ValueError("No locator") # TODO

        # # trans
        # trans_data = retarget_translation(src_root, tgt_root,
        #                                   height_ratio)
        # # rot
        # retarget_rotation(src_joints_common, tgt_joints_common, src_joints_origin, tgt_joints_origin,
        #                   Tpose_trfs, 
        #                   src_Tpose_rots, tgt_Tpose_rots, src_indices, tgt_indices, 
        #                     len(trans_data))
    
    ''' export '''
    # Remove source locator
    if src_locator is not None:
        delete_locator_and_hierarchy(src_locator)
    else:
        delete_locator_and_hierarchy(src_joints_common[0])
    
    # meshes
    cmds.delete(src_meshes)

    # rename tgt joint
    for joint in tgt_joints_original_name:
        cmds.rename('tgt:'+joint, joint)

    # rename tgt joints
    # TODO: locator의 이름이 같을때 대응할수없음
    # tgt_locator = remove_namespace_for_joints([tgt_locator])[0]

    # Run the function
    delete_all_transform_nodes()

    # export
    print(">>({}, {}) ->  {}".format(sourceChar, sourceMotion, targetChar))
    export(args, targetChar, targetMotion)
    
    # end
    maya.standalone.uninitialize()

    # end time
    end_time = time.time()
    execution_time = end_time - start_time
    minutes = int(execution_time // 60)
    seconds = execution_time % 60
    print(f">> Execution time: {execution_time:.3f}, {minutes}m {seconds:.3f}s")

if __name__=="__main__":
    main()
