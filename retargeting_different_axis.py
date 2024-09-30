"""
Usage:
mayapy retargeting_different_axis.py --sourceChar "" --sourceMotion "" --targetChar ""

example:
mayapy retargeting_different_axis.py --sourceChar "./models/Asooni/Asooni.fbx" --sourceMotion "./motions/Asooni/Super shy - New Jeans_RT1226.fbx" --targetChar "./models/Adori/Adori.fbx"\
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
    print(">> retargeting start")
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        # print("no maya pluginInfo")
        cmds.loadPlugin('fbxmaya')
    
    # name
    args = get_args()
    sourceMotion = args.sourceMotion
    targetMotion = sourceMotion.split('/')[-1].split('.')[0]
    targetChar = args.targetChar.split('/')[-1].split('.')[0]
    print(">>({}, {}) ->  {}".format(\
        args.sourceChar, sourceMotion, targetChar))


    ''' tgt '''
    # character
    mel.eval('FBXImport -f"{}"'.format(args.targetChar))

    # joints
    tgt_joints, tgt_root_joint = get_tgt_joints()

    # tgt locator
    tgt_locator_list = cmds.ls(type='locator')
    if len(tgt_locator_list)!=0:
        tgt_locator, tgt_locator_rot, tgt_locator_scale = get_locator(tgt_locator_list)
    else:
        tgt_locator = None
    print(">> tgt loaded")

    # rename joints
    # if namespace is already exist, skip it
    if ":" in tgt_joints[0]:
        pass
    else:
        tgt_joints = add_namespace_for_joints(tgt_joints, "tgt")
    # renamed by template 
    tgt_joint_renamed = rename_joint_by_template(tgt_joints)

    # meshes
    tgt_meshes = cmds.ls(type='mesh')
    tgt_meshes = add_namespace_for_meshes(tgt_meshes, "tgt_mesh")


    ''' src '''
    if args.sourceChar != "":
        # source character 있을때
        mel.eval('FBXImport -f"{}"'.format(args.sourceChar))
        
        src_joints = get_src_joints(tgt_joints)

        src_joints, tgt_joints, _, parent_indices = get_common_src_tgt_joint_hierarchy(src_joints, tgt_joints, tgt_joint_renamed)
        
        if tgt_locator is not None:
            prerotations = get_prerotations(tgt_joints, tgt_locator, tgt_locator_rot,)
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

        src_joints, tgt_joints, _, parent_indices = get_common_src_tgt_joint_hierarchy(src_joints, tgt_joints, tgt_joint_renamed)

        # Tpose trf
        Tpose_trfs = get_Tpose_trf(src_joints, tgt_joints)
    
    # get root height scale 
    src_root = src_joints[0]
    src_hip_height = cmds.xform(src_root, query=True, translation=True, worldSpace=True)[1]
    tgt_root = tgt_joints[0]
    tgt_hip_height = cmds.xform(tgt_root, query=True, translation=True, worldSpace=True)[1]
    height_ratio = tgt_hip_height / src_hip_height

    # locator and joints
    locators_list = cmds.ls(type='locator')
    src_locator_list = list(set(locators_list) - set(tgt_locator_list))
    if len(src_locator_list)!=0:
        src_locator, src_locator_rot, src_locator_scale = get_locator(src_locator_list)
    else:
        src_locator = None

    # src meshes
    all_meshes = cmds.ls(type='mesh')
    src_meshes = list(set(all_meshes) - set(tgt_meshes))
    print(">> src loaded")


    ''' retarget '''
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
        retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, \
                          len(trans_data), src_locator_rot, tgt_locator_rot,\
                            prerotations)
    else:
        print(">> retarget without locator")
        # trans
        trans_data = retarget_translation(src_joints[0], tgt_joints[0],
                                          height_ratio)
        # rot
        retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, len(trans_data))
    print(">> retargeted")
    

    ''' export '''
    # Remove source locator
    # if src_locator is not None:
    #     delete_locator_and_hierarchy(src_locator)
    # else:
    #     delete_locator_and_hierarchy(src_joints[0])
    
    # meshes
    cmds.delete(src_meshes)

    # rename tgt joints
    tgt_joints = remove_namespace_for_joints(tgt_joints)

    # Run the function
    delete_all_transform_nodes()

    # free
    if tgt_locator is not None:
        top_joint = tgt_locator
    else:
        tgt_root_joint = tgt_joints[0]
        top_joint = tgt_root_joint
    # freeze_and_bake(top_joint)
    print(">> retargeting from source: (char {}, motion {})".format(args.sourceChar, sourceMotion))
    export(args, targetChar, targetMotion)
    
    # end
    maya.standalone.uninitialize()

if __name__=="__main__":
    main()
