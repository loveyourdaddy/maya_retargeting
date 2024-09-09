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
    print(">> retargeting start")
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        # print("no maya pluginInfo")
        cmds.loadPlugin('fbxmaya')
    
    # name
    args = get_args()
    sourceMotion = args.sourceMotion
    targetMotion = sourceMotion.split('/')[-1].split('.')[0]
    targetChar = args.targetChar.split('/')[-1].split('.')[0]
    print(">> in retargeting, srcMotion {} of srcChar {} -> tgtChar {}".format(\
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
    print(">> tgt loaded")

    # rename joints
    # if namespace is already exist, skip it
    if ":" in tgt_joints[0]:
        pass
    else:
        tgt_joints = add_namespace_for_joints(tgt_joints, "tgt")
    tgt_joints_refined = refine_joint_name(tgt_joints)

    # meshes
    tgt_meshes = cmds.ls(type='mesh')
    tgt_meshes = add_namespace_for_meshes(tgt_meshes, "tgt_mesh")

    # Get prerot
    # (locator, joint들의) local rotation을 저장 후 나중에 복원.
    angle_origins = []
    prerotations = []
    if tgt_locator is not None:
        cmds.xform(tgt_locator, ro=(0,0,0), q=False, ws=False)
    for joint in tgt_joints:
        # zero rotation을 만들어야하는게 아닐까?
        angle_origin = cmds.xform(joint, q=True, ws=False, ro=True)

        # set zero rot and get world rot 
        cmds.xform(joint, ro=(0,0,0), q=False, ws=False)
        prerot = np.transpose(np.array(cmds.xform(joint, q=True, ws=True, matrix=True)).reshape(4,4)[:3,:3])
        
        # 원래 rotation으로 돌려두기
        # cmds.xform(joint, ro=tuple(angle_origin), q=False, ws=False)
        angle_origins.append(angle_origin)
        prerotations.append(prerot)

    # 기존 값으로 돌려주기
    if tgt_locator is not None:
        cmds.xform(tgt_locator, ro=(tgt_locator_rot), q=False, ws=False)
    for j, joint in enumerate(tgt_joints):
        angle_origin = angle_origins[j]
        cmds.xform(joint, ro=tuple(angle_origin), q=False, ws=False)

    ''' src '''
    # source character 있을때
    import pdb; pdb.set_trace()
    if args.sourceChar != "":
        mel.eval('FBXImport -f"{}"'.format(args.sourceChar))
        src_joints, tgt_joints, _, parent_indices, Tpose_trfs = get_joint_hierarchy_and_Tpose_trf(tgt_joints, tgt_joints_refined)
        
        # import src motion
        mel.eval('FBXImport -f"{}"'.format(sourceMotion))

    # source character가 없을때, 0 frame을 Tpose로 사용. 
    if args.sourceChar == "": 
        print(">> no source character")
    
        # import src motion
        mel.eval('FBXImport -f"{}"'.format(sourceMotion))
        src_joints, tgt_joints, _, parent_indices, Tpose_trfs = get_joint_hierarchy_and_Tpose_trf(tgt_joints, tgt_joints_refined)

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
    # Translation root
    if False:
        translate = np.array([300, 0, 0])
    else:
        translate = None

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
                                          translate=translate)
        # rot
        retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, \
                          len(trans_data), src_locator_rot, tgt_locator_rot,\
                            prerotations)
    else:
        print(">> retarget without locator")
        # trans
        trans_data = retarget_translation(src_joints[0], tgt_joints[0], 
                                          translate=translate)
        # rot
        retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, len(trans_data))
    # import pdb; pdb.set_trace()
    print(">> retargeted")
    # Remove source locator 
    # print(src_locator)
    if src_locator is not None:
        delete_locator_and_hierarchy(src_locator)
    else:
        delete_locator_and_hierarchy(src_joints[0])
    
    # meshes
    cmds.delete(src_meshes)

    # rename tgt joints
    # import pdb; pdb.set_trace()
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
    print(">> retargeting from source: char {}, motion {}".format(args.sourceChar, sourceMotion))
    export(args, targetChar, targetMotion)
    
    # end
    maya.standalone.uninitialize()

if __name__=="__main__":
    main()
