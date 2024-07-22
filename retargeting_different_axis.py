import maya.cmds as cmds
import maya.standalone
from functions.parser import *
from functions.character import *
from functions.motion import *
from functions.maya import *

def main():
    maya.standalone.initialize(name='python')

    # Load the FBX plugin
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        cmds.loadPlugin('fbxmaya')
    
    # name 
    args = get_args()
    sourceMotion = args.sourceMotion
    sourceChar = sourceMotion.split('/')[2]
    targetMotion = sourceMotion.split('/')[-1].split('.')[0]
    targetChar = args.targetChar.split('/')[3].split('.')[0]

    ''' tgt '''
    # character
    mel.eval('FBXImport -f"{}"'.format(args.targetChar))

    # joints
    # tgt
    tgt_joints, tgt_root_joint = get_tgt_joints()
    # tgt locator
    tgt_locator = cmds.ls(type='locator')
    if len(tgt_locator)!=0:
        tgt_locator, tgt_locator_rot, tgt_locator_scale = get_locator(tgt_locator)

    ''' src '''
    import_Tpose(sourceChar, targetChar)
    src_joints = get_src_joints(tgt_joints)

    # refine name 
    tgt_joints_refined = refine_joint_name(tgt_joints)
    src_joints, tgt_joints_refined, parent_indices, _, tgt_indices = refine_joints(src_joints, tgt_joints_refined, tgt_joints) 
    
    # tgt_joints
    # refined joint에서 인덱스을 얻을 후, tgt joints에서 뽑기
    tgt_joints = [tgt_joints[i] for i in tgt_indices]

    # Tpose trf
    Tpose_trfs = get_Tpose_trf(src_joints, tgt_joints)
    
    ''' import src motion '''
    mel.eval('FBXImport -f"{}"'.format(sourceMotion))

    ''' retarget '''
    if tgt_locator is not None and len(tgt_locator)!=0:
        print("retarget with locator")
        trans_data = retarget_translation(src_joints[0], tgt_joints[0], tgt_locator, tgt_locator_rot, tgt_locator_scale)
        retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, len(trans_data), tgt_locator_rot)
    else:
        print("retarget without locator")
        trans_data = retarget_translation(src_joints[0], tgt_joints[0])
        retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, len(trans_data))

    # free
    if len(tgt_locator)!=0:
        top_joint = tgt_locator
    else:
        top_joint = tgt_root_joint
    
    freeze_and_bake(top_joint)
    export(args, targetChar, targetMotion)

    # end
    maya.standalone.uninitialize()

if __name__=="__main__":
    main()

"""
usage
- mayapy retargeting_different_axis.py --src_motion_path "" --tgt_char_path ""

Window 
D:\_Program\AutoDesk\Maya2023\Maya2023\bin\mayapy retargeting_different_axis.py 
--sourceMotion "./motions/Asooni/animation_before_edit/Go Hard - TWICE_002_RT0118.fbx" 
--targetChar "./models/_General/1.Adori/SKM_ADORI_0424.fbx"

Mac
/Applications/Autodesk/maya2025/Maya.app/Contents/MacOS/mayapy retargeting_different_axis.py --sourceMotion './motions/Asooni/animation_before_edit/Go Hard - TWICE_002_RT0118.fbx' --targetChar './models/_General/1.Adori/SKM_ADORI2.0_0424.fbx'
"""
