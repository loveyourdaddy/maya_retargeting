import maya.standalone
maya.standalone.initialize(name='python')
import maya.cmds as cmds
import maya.mel as mel
import argparse
import os 
from retargeting_different_axis import find_root_joints, get_joint_hierarchy, refine_joints, \
    get_args, get_keyframe_data, get_array_from_keyframe_data, set_keyframe, \
    src_template_joints, tgt_template_joints

"""
retarget to other character (not for own)

usage
- mayapy import_export_fbx.py --src_motion_path "" --tgt_char_path "" --tgt_motion_path ""
"""
# Asooni -> Adori
# D:\_Program\AutoDesk\Maya2023\Maya2023\bin\mayapy import_export_with_dict.py --sourceMotion "./motions/Asooni/animation/0048_Basic Roll_01_RT0104.fbx" --targetChar "./models/Dancstruct/normalized/3_ASOONI_1207_0617.fbx"


# Load the FBX plugin
if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
    cmds.loadPlugin('fbxmaya')

# load source
args = get_args()

""" load target char -> load motion """
""" load target char """
targetChar = args.targetChar
mel.eval('FBXImport -f "{}"'.format(targetChar))
target_char = targetChar.split('/')[-1].split('.')[0]
 
# tgt joint hierarchy 
tgt_joints = cmds.ls(type='joint')
root_joint = find_root_joints(tgt_joints)
tgt_joint_hierarchy = get_joint_hierarchy(root_joint)
tgt_joint_hierarchy = refine_joints(tgt_joint_hierarchy, tgt_template_joints)
print("{}".format(len(tgt_joint_hierarchy))) # , tgt_joint_hierarchy

""" load source motion """
sourceMotion = args.sourceMotion
mel.eval('FBXImport -f"{}"'.format(sourceMotion))
target_motion = sourceMotion.split('/')[-1].split('.')[0]

# src joint hierarchy
src_joints = cmds.ls(type='joint')
src_joints = list(set(src_joints) - set(tgt_joints))
root_joint = find_root_joints(src_joints)
src_joint_hierarchy = get_joint_hierarchy(root_joint)
src_joint_hierarchy = refine_joints(src_joint_hierarchy, src_template_joints)
print("{}".format(len(src_joint_hierarchy))) # src_joint_hierarchy

for j, (src_joint, tgt_joint) in enumerate(zip(src_joint_hierarchy, tgt_joint_hierarchy)):
    trans_data, keyframe_data = get_keyframe_data(src_joint)
    
    # root translation
    if j==0:
        trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
        trans_data = get_array_from_keyframe_data(trans_data, trans_attr)
        set_keyframe(tgt_joint, trans_data, trans_attr)
    
    # joint rotation 
    rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
    rot_data = get_array_from_keyframe_data(keyframe_data, rot_attr)
    set_keyframe(tgt_joint, rot_data, rot_attr)

# export
output_dir = args.tgt_motion_path + target_char
os.makedirs(output_dir, exist_ok=True)
export_file = output_dir+'/'+target_motion+'.fbx'
mel.eval('FBXExport -f"{}"'.format(export_file))

# uninitalize
maya.standalone.uninitialize()
print("File export to ", export_file)
