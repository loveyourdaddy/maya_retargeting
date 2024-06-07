import maya.standalone
maya.standalone.initialize(name='python')
import maya.cmds as cmds
import maya.mel as mel
import argparse
import os 

"""
usage
- mayapy import_export_fbx.py --src_motion_path "" --tgt_char_path "" --tgt_motion_path ""
"""
# mayapy import_export_fbx.py --sourceMotion "./motions/Adori/animation/0055_Freestyle002_03_RT0214.fbx" --targetChar "./models/Dancstruct/SKM_ADORI_0229.fbx"
# D:\_Program\AutoDesk\Maya2023\Maya2023\bin\mayapy

def get_joint_hierarchy(root_joint):
    hierarchy = []

    def traverse_joint(joint):
        children = cmds.listRelatives(joint, children=True, type='joint') or []
        hierarchy.append(joint)
        for child in children:
            traverse_joint(child)

    traverse_joint(root_joint)
    return hierarchy

def find_root_joints(all_joints):
    root_joints = []
    
    for joint in all_joints:
        parents = cmds.listRelatives(joint, parent=True)
        
        if not parents or cmds.nodeType(parents[0]) != 'joint': 
            root_joints.append(joint)
    
    return root_joints[0] # should be one 

def refine_joints(joints, template_joints):
    refined_joints = []
    for joint in joints:
        for template_joint in template_joints:
            if template_joint in joint:
                refined_joints.append(joint)
                break
    return refined_joints

def get_keyframe_data(joint):
    keyframe_data = {'rotateX': [], 'rotateY': [], 'rotateZ': [], 
                     'translateX': [], 'translateY': [], 'translateZ': []}    
    for attr in keyframe_data.keys():
        keyframe_count = cmds.keyframe(f'{joint}.{attr}', query=True, keyframeCount=True)
        if keyframe_count > 0:
            times = cmds.keyframe(f'{joint}.{attr}', query=True, timeChange=True)
            values = cmds.keyframe(f'{joint}.{attr}', query=True, valueChange=True)
            keyframe_data[attr] = list(zip(times, values))
    
    return keyframe_data

def set_keyframe_data(joint, keyframe_data):
    for attr, keyframes in keyframe_data.items():
        for time, value in keyframes:
            cmds.setKeyframe(joint, attribute=attr, time=time, value=value)

# dict 
template_joints = \
    ["Hips","Spine","Spine1","Spine2","Neck","Head","HeadTop_End",
    "LeftShoulder","LeftArm","LeftForeArm","LeftHand",
    "RightShoulder","RightArm","RightForeArm","RightHand",
    "LeftUpLeg","LeftLeg","LeftFoot","LeftToeBase", "LeftToe_End",
    "RightUpLeg","RightLeg","RightFoot","RightToeBase", "RightToe_End"]
# character의 이름을 포함하기?"Armature", "ADORI", 

# Load the FBX plugin
if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
    cmds.loadPlugin('fbxmaya')

def get_parser():
    parser = argparse.ArgumentParser(description='Import an FBX file into Maya')
    parser.add_argument('--sourceMotion', type=str, default="./motions/Adori/animation/0055_Freestyle002_03_RT0214.fbx")
    parser.add_argument('--targetChar', type=str, default="./models/Dancstruct/SKM_ADORI_0229.fbx")
    parser.add_argument('--tgt_motion_path', type=str, default="./output/")
    return parser

def get_args():
    parser = get_parser()
    return parser.parse_args()


# load source
args = get_args()

"""
order :
load target char -> load motion 
"""
# load target 
targetChar = args.targetChar
mel.eval('FBXImport -f"{}"'.format(targetChar))
target_char = targetChar.split('/')[-1].split('.')[0]
# tgt joint hierarchy
tgt_joints = cmds.ls(type='joint')
root_joint = find_root_joints(tgt_joints)
tgt_joint_hierarchy = get_joint_hierarchy(root_joint)
tgt_joint_hierarchy = refine_joints(tgt_joint_hierarchy, template_joints)
tgt_locator = cmds.ls(type='locator')


# load motion 
sourceMotion = args.sourceMotion
mel.eval('FBXImport -f"{}"'.format(sourceMotion))
target_motion = sourceMotion.split('/')[-1].split('.')[0]
# src joint hierarchy
src_joints = cmds.ls(type='joint')
src_joints = list(set(src_joints) - set(tgt_joints))
root_joint = find_root_joints(src_joints)
src_joint_hierarchy = get_joint_hierarchy(root_joint)
src_joint_hierarchy = refine_joints(src_joint_hierarchy, template_joints)
# src locator 
src_locator = cmds.ls(type='locator')
src_locator = list(set(src_locator) - set(tgt_locator))
src_locator = src_locator[0].replace("Shape","")
src_locator_translation = cmds.xform(src_locator, q=True, ws =True, ro=True)


# set to target char
# locator
tgt_locator = tgt_locator[0].replace("Shape","")
cmds.xform(tgt_locator, ws=False, ro=src_locator_translation)
# joints 
for src_joint, tgt_joint in zip(src_joint_hierarchy, tgt_joint_hierarchy):
    keyframe_data = get_keyframe_data(src_joint)
    set_keyframe_data(tgt_joint, keyframe_data)

# freeze
incoming_connections = {}
for attr in ['rotateX', 'rotateY', 'rotateZ']:
    full_attr = f"Armature.{attr}"
    connections = cmds.listConnections(full_attr, s=True, d=False, p=True)
    if connections:
        print(connections)
        incoming_connections[attr] = connections[0]
        cmds.disconnectAttr(connections[0], full_attr)
# bake 
cmds.bakeResults("Armature", simulation=True, t=(cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True)), sampleBy=1, oversamplingRate=1, disableImplicitControl=True, preserveOutsideKeys=True, sparseAnimCurveBake=False, removeBakedAnimFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=False, shape=True)

# export 
output_dir = args.tgt_motion_path + target_char
os.makedirs(output_dir, exist_ok=True)
export_file = output_dir+'/'+target_motion+'.fbx'
mel.eval('FBXExport -f"{}"'.format(export_file))

maya.standalone.uninitialize()

print("File export to ", export_file)
