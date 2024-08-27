"""
Usage:
mayapy retargeting_different_axis.py --sourceChar "" --sourceMotion "" --targetChar ""

example:
mayapy retargeting_different_axis.py --sourceChar "./models/Asooni/Asooni.fbx" --sourceMotion "./motions/Asooni/Super shy - New Jeans_RT1226.fbx" --targetChar "./models/Adori/Adori.fbx"

Requirement:
1. characters of Source and target : Tpose상태를 가정 
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
    print("retargeting start")
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        # print("no maya pluginInfo")
        cmds.loadPlugin('fbxmaya')
    
    # name
    args = get_args()
    sourceMotion = args.sourceMotion
    targetMotion = sourceMotion.split('/')[-1].split('.')[0]
    targetChar = args.targetChar.split('/')[-1].split('.')[0]
    print("in retargeting, srcMotion {} of srcChar {} -> tgtChar {}".format(\
        sourceMotion, args.sourceChar, targetChar))


    ''' tgt '''
    # character
    # print("args.targetChar:", args.targetChar)
    mel.eval('FBXImport -f"{}"'.format(args.targetChar))

    # joints
    tgt_joints, tgt_root_joint = get_tgt_joints()


    # tgt locator
    tgt_locator_list = cmds.ls(type='locator')
    if len(tgt_locator_list)!=0:
        tgt_locator, tgt_locator_rot, tgt_locator_scale = get_locator(tgt_locator_list)
    else:
        tgt_locator = None

    # joints
    # if namespace is already exist, skip it 
    if ":" in tgt_joints[0]:
        pass
    else:
        tgt_joints = add_namespace_for_joints(tgt_joints, "tgt")
    tgt_joints_refined = refine_joint_name(tgt_joints)


    # meshes 
    tgt_meshes = cmds.ls(type='mesh')
    tgt_meshes = add_namespace_for_meshes(tgt_meshes, "tgt_mesh")


    ''' src '''
    mel.eval('FBXImport -f"{}"'.format(args.sourceChar))
    src_joints = get_src_joints(tgt_joints)

    # refine name
    src_joints, tgt_joints_refined, parent_indices, _, tgt_indices = refine_joints(src_joints, tgt_joints_refined, tgt_joints) 

    # tgt_joints
    # refined joint에서 인덱스을 얻을 후, tgt joints에서 뽑기
    tgt_joints = [tgt_joints[i] for i in tgt_indices]

    # Tpose trf
    Tpose_trfs = get_Tpose_trf(src_joints, tgt_joints)

    # import src motion 
    mel.eval('FBXImport -f"{}"'.format(sourceMotion))
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


    ''' retarget '''
    # Translation root
    if False:
        translate = np.array([300, 0, 0])
    else:
        translate = None

    if src_locator is not None or tgt_locator is not None:
        # print("retarget with locator")
        # 예외처리
        if src_locator is None:
            src_locator_rot, src_locator_scale = None, None
        if tgt_locator is None:
            tgt_locator_rot, tgt_locator_scale = None, None
        
        # trans 
        trans_data = retarget_translation(src_joints[0], tgt_joints[0],\
                                          src_locator, src_locator_rot, src_locator_scale,\
                                          tgt_locator, tgt_locator_rot, tgt_locator_scale,\
                                          translate=translate)
        # rot
        retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, len(trans_data), src_locator_rot, tgt_locator_rot)
    else:
        # print("retarget without locator")
        # trans
        trans_data = retarget_translation(src_joints[0], tgt_joints[0], 
                                          translate=translate)
        # rot
        retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, len(trans_data))
    
    # Remove source locator 
    if src_locator is not None:
        delete_locator_and_hierarchy(src_locator)
    else:
        delete_locator_and_hierarchy(src_joints[0])
        
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
    freeze_and_bake(top_joint)
    export(args, targetChar, targetMotion)
    
    # end
    maya.standalone.uninitialize()

if __name__=="__main__":
    main()
