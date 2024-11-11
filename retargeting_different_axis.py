"""
Usage:
mayapy retargeting_different_axis.py --sourceMotion "" --targetChar ""

example:
mayapy retargeting_different_axis.py --sourceMotion "./motions/Asooni/Super shy - New Jeans_RT1226.fbx" --targetChar "./models/Adori/Adori.fbx"
"""

import maya.cmds as cmds
import maya.standalone
from functions.parser import *
from functions.character import *
from functions.motion import *
from functions.maya import *

def main():
    maya.standalone.initialize(name='python')

    # Load the FBX plugin
    print(">> Retargeting start")
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        cmds.loadPlugin('fbxmaya')
    
    def get_name(name):
        # path 제거 
        name = name.split('/')[-1]
        # format 제거
        format = "." + name.split('.')[-1]
        return name.replace(format, "")

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
    tgt_joints, tgt_root_joint = get_tgt_joints()
    tgt_Tpose_rots = get_Tpose_local_rotations(tgt_joints)
    parent_node = cmds.listRelatives(tgt_root_joint, parent=True, shapes=True)[-1]


    # rename joint
    # add namespace joints (in maya also)
    tgt_joints_origin_namespace = add_namespace_for_joints(tgt_joints, "tgt")
    tgt_joints = tgt_joints_origin_namespace

    # renamed by template
    tgt_joints_renamed_by_template = rename_joint_by_template(tgt_joints)


    # locator
    # import pdb; pdb.set_trace()
    if parent_node is not None:
        tgt_locator, tgt_locator_rot, tgt_locator_scale = get_locator(parent_node)
    else:
        tgt_locator = None
    tgt_locator = add_namespace_for_joints([tgt_locator], "tgt")[0]
    tgt_locator_list = [tgt_locator, tgt_locator+'Shape']


    # meshes
    tgt_meshes = cmds.ls(type='mesh')
    tgt_meshes = add_namespace_for_meshes(tgt_meshes, "tgt_mesh")
    print(">> tgt loaded")


    ''' src '''
    sourceChar_path = './models/' + sourceChar + '/' + sourceChar + '.fbx'
    # if source character exist 
    if os.path.exists(sourceChar_path):
        mel.eval('FBXImport -f"{}"'.format(sourceChar_path))
        
        src_joints = get_src_joints(tgt_joints)
        src_Tpose_rots = get_Tpose_local_rotations(src_joints)
        src_joints_origin = src_joints

        src_joints, tgt_joints, _, parent_indices = get_common_src_tgt_joint_hierarchy(src_joints, tgt_joints, tgt_joints_renamed_by_template)
        
        if tgt_locator is not None:
            prerotations = get_prerotations(tgt_joints, tgt_locator, tgt_locator_rot)
        else:
            prerotations = get_prerotations(tgt_joints)

        # Tpose trf
        Tpose_trfs = get_Tpose_trf(src_joints, tgt_joints, prerotations)

        # import src motion
        mel.eval('FBXImport -f"{}"'.format(sourceMotion))
    else: # args.sourceChar == "": 
        # source character가 없을때, 0 frame을 Tpose로 사용. 
        print(">> no source character")
    
        # import src motion
        mel.eval('FBXImport -f"{}"'.format(sourceMotion))
        src_joints = get_src_joints(tgt_joints)
        src_Tpose_rots = get_Tpose_local_rotations(src_joints)

        src_joints, tgt_joints, _, parent_indices = get_common_src_tgt_joint_hierarchy(src_joints, tgt_joints, tgt_joints_renamed_by_template)

        # Tpose trf
        Tpose_trfs = get_Tpose_trf(src_joints, tgt_joints)

    # get root height scale
    src_root = src_joints[0]
    src_hip_height = cmds.xform(src_root, query=True, translation=True, worldSpace=True)[1]
    tgt_root = tgt_joints[0]
    tgt_hip_height = cmds.xform(tgt_root, query=True, translation=True, worldSpace=True)[1]

    # 만약 hip height가 0이면 발끝부터 root 까지의 거리를 계산
    # if src_hip_height < 0.01:
    #     src_hip_height = get_distance_from_toe_to_root(src_joints)
    if tgt_hip_height < 0.01:
        tgt_hip_height = get_distance_from_toe_to_root(tgt_joints, tgt_root)

    # ratio
    height_ratio = tgt_hip_height / src_hip_height


    # locator and joints
    locators_list = cmds.ls(type='locator')
    src_locator_list = list(set(locators_list) - set(tgt_locator_list))
    if len(src_locator_list)!=0:
        src_locator, src_locator_rot, src_locator_scale = get_locator(src_locator_list[0])
    else:
        src_locator = None

    # src meshes
    all_meshes = cmds.ls(type='mesh')
    src_meshes = list(set(all_meshes) - set(tgt_meshes))
    print(">> src loaded")


    ''' retarget '''
    # 둘 중 하나라도  cloator가 있는 경우 
    if src_locator is not None or tgt_locator is not None:
        print(">> retarget with locator")

        # 예외처리
        if src_locator is None:
            src_locator_rot, src_locator_scale = None, None
        if tgt_locator is None:
            tgt_locator_rot, tgt_locator_scale = None, None
        
        # trans 
        trans_data = retarget_translation(src_joints[0], tgt_joints[0],\
                                          src_locator, src_locator_rot, src_locator_scale,\
                                          tgt_locator, tgt_locator_rot, tgt_locator_scale,\
                                            height_ratio)
        # rot
        retarget_rotation(src_joints, tgt_joints, src_joints_origin, tgt_joints_origin_namespace, 
                          Tpose_trfs, parent_indices, 
                          src_Tpose_rots, tgt_Tpose_rots,
                          len(trans_data), src_locator_rot, tgt_locator_rot,\
                            prerotations)
    # 둘다 locator가 없는 경우 TODO: 합치기. 
    else:
        print(">> retarget without locator")
        # trans
        trans_data = retarget_translation(src_joints[0], tgt_joints[0],
                                          height_ratio)
        # rot
        retarget_rotation(src_joints, tgt_joints, src_joints_origin, tgt_joints_origin_namespace,
                          Tpose_trfs, parent_indices, tgt_Tpose_rots,
                            len(trans_data))
    
    ''' export '''
    # Remove source locator
    if src_locator is not None:
        delete_locator_and_hierarchy(src_locator)
    else:
        delete_locator_and_hierarchy(src_joints[0])
    
    # meshes
    cmds.delete(src_meshes)

    # rename tgt joints
    tgt_locator = remove_namespace_for_joints([tgt_locator])[0]
    tgt_joints = remove_namespace_for_joints(tgt_joints)

    # Run the function
    delete_all_transform_nodes()

    # free
    # if tgt_locator is not None:
    #     top_joint = tgt_locator
    # else:
    #     tgt_root_joint = tgt_joints[0]
    #     top_joint = tgt_root_joint
    # freeze_and_bake(top_joint) 

    # export
    print(">> retargeting from source: (char {}, motion {})".format(sourceChar, sourceMotion))
    export(args, targetChar, targetMotion)
    
    # end
    maya.standalone.uninitialize()

if __name__=="__main__":
    main()
