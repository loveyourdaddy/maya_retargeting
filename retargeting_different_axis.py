import maya.standalone
maya.standalone.initialize(name='python')
import maya.cmds as cmds
import maya.mel as mel
import argparse
import os 
import copy

"""
usage
- mayapy retargeting_different_axis.py --src_motion_path "" --tgt_char_path "" --tgt_motion_path ""
"""
# mayapy retargeting_different_axis.py --sourceMotion "./motions/Adori/animation/0055_Freestyle002_03_RT0214.fbx" --targetChar "./models/Dancstruct/SKM_ADORI_0229.fbx"
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
            if template_joint in joint and \
                "Thumb" not in joint and \
                "Index" not in joint and \
                "Middle" not in joint and \
                "Ring" not in joint and \
                "Pinky" not in joint:
                refined_joints.append(joint)
                break
    
    return refined_joints

def refine_joint_name(joints):
    form = "ACHID:" # list로 바꾸기
    ret_joints = [] 
    for joint in joints:
        if form in joint:
            joint = joint.replace(form, "")
        ret_joints.append(joint)
    return ret_joints

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

def get_Tpose_data(keyframe_data):
    Tpose_data = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
    frame = 0
    for attr in keyframe_data.keys():
        Tpose_data[attr] = keyframe_data[attr][frame][1]
    return Tpose_data

def get_delta_rotation(keyframe_data, src_Tpose):
    rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}

    delta_data = []
    for attr in rot_attr.keys():
        delta = []
        for fid, data_perframe in enumerate(keyframe_data[attr]):
            delta.append(data_perframe[1] - src_Tpose[attr])
        delta_data.append(delta)
    
    return delta_data # [attr 3, frames]

def set_translate_keyframe(joint, keyframe_data):
    for attr, keyframes in keyframe_data.items():
        # set only translate
        if attr=="rotateX" or attr=="rotateY" or attr=="rotateZ":
            continue
        for tid, (time, value) in enumerate(keyframes):
            cmds.setKeyframe(joint, attribute=attr, time=time, value=value)

def set_rotation_keyframe(joint, keyframe_data, src_keyframe):
    for attr, keyframes in src_keyframe.items():
        if attr=="translateX" or attr=="translateY" or attr=="translateZ":
            continue
        
        if attr=="rotateX":
            attr_idx=0
        elif attr=="rotateY":
            attr_idx=1
        elif attr=="rotateZ":
            attr_idx=2
        
        # print("{} {}".format(attr, keyframe_data[attr_idx][0]))
        for tid, (time, _) in enumerate(keyframes):
            value = keyframe_data[attr_idx][tid]
            cmds.setKeyframe(joint, attribute=attr, time=time, value=value)

def get_parser():
    parser = argparse.ArgumentParser(description='Import an FBX file into Maya')
    parser.add_argument('--sourceMotion', type=str, default="./motions/Adori/animation/0055_Freestyle002_03_RT0214.fbx")
    parser.add_argument('--targetChar', type=str, default="./models/Dancstruct/SKM_ADORI_0229.fbx")
    parser.add_argument('--tgt_motion_path', type=str, default="./output/")
    return parser

def get_args():
    parser = get_parser()
    return parser.parse_args()

# dict 
template_joints = \
    ["Hips","Spine","Spine1","Spine2","Neck","Head","HeadTop_End",
    "LeftShoulder","LeftArm","LeftForeArm","LeftHand",
    "RightShoulder","RightArm","RightForeArm","RightHand",
    "LeftUpLeg","LeftLeg","LeftFoot","LeftToeBase", "LeftToe_End",
    "RightUpLeg","RightLeg","RightFoot","RightToeBase", "RightToe_End"]

# Load the FBX plugin
if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
    cmds.loadPlugin('fbxmaya')

args = get_args()

""" load target """
targetChar = args.targetChar
mel.eval('FBXImport -f"{}"'.format(targetChar))
target_char = targetChar.split('/')[-1].split('.')[0]
# tgt joint hierarchy
tgt_joints = cmds.ls(type='joint')
root_joint = find_root_joints(tgt_joints)
tgt_joint_hierarchy = get_joint_hierarchy(root_joint)
tgt_joint_hierarchy = refine_joints(tgt_joint_hierarchy, template_joints)
# get locator rotation 
tgt_locator = cmds.ls(type='locator')
tgt_locator = tgt_locator[0].replace("Shape","")

# Tpose of tgt (inital pose for updating delta)
tgt_Tpose = [[0,0,0] for _ in range(len(tgt_joint_hierarchy))]
# other joint: tgt load할때 얻기
for i, joint in enumerate(tgt_joint_hierarchy):
    tgt_Tpose[i] = cmds.xform(joint, q=True,ws=False, ro=True)

""" load motion """
sourceMotion = args.sourceMotion
mel.eval('FBXImport -f"{}"'.format(sourceMotion))
target_motion = sourceMotion.split('/')[-1].split('.')[0]
# src joint hierarchy
src_joints = cmds.ls(type='joint')
src_joints = list(set(src_joints) - set(tgt_joints))
root_joint = find_root_joints(src_joints)
src_joint_hierarchy = get_joint_hierarchy(root_joint)
src_joint_hierarchy = refine_joints(src_joint_hierarchy, template_joints)

# find common joints 
tgt_joint_hierarchy_refined = refine_joint_name(tgt_joint_hierarchy)
joint_hierarchy = []
for src_joint in src_joint_hierarchy:
    if src_joint in tgt_joint_hierarchy_refined:
        joint_hierarchy.append(src_joint)

src_joint_index, tgt_joint_index = [], []
for joint in joint_hierarchy:
    src_joint_index.append(src_joint_hierarchy.index(joint))
    tgt_joint_index.append(tgt_joint_hierarchy_refined.index(joint))
# print("{}:{}".format(src_joint_index, tgt_joint_index))

# src locator 
src_locator = cmds.ls(type='locator')
src_locator = list(set(src_locator) - set(tgt_locator))
src_locator = src_locator[0].replace("Shape","")
src_locator_translation = cmds.xform(src_locator, q=True, ws =True, ro=True)

# hip joint: inverse of locator rotation 
for i in range(3):
    tgt_Tpose[0][i] = -src_locator_translation[i]


""" set to target char """
# locator
print("src_locator_translation ",src_locator_translation)
cmds.xform(tgt_locator, ws=False, ro=src_locator_translation)
# joints 
print("src_joint_hierarchy:", src_joint_hierarchy[src_joint_index])
print("tgt_joint_hierarchy", tgt_joint_hierarchy[tgt_joint_index])

for j, (src_joint, tgt_joint) in enumerate(zip(src_joint_hierarchy[src_joint_index], tgt_joint_hierarchy[tgt_joint_index])):
    keyframe_data = get_keyframe_data(src_joint)
    # root update 
    set_translate_keyframe(tgt_joint, keyframe_data)

    # get src delta rotation 
    """ assumption: first frame is Tpose  """
    src_Tpose = get_Tpose_data(keyframe_data)
    # Tuple -> list 
    src_delta_data = get_delta_rotation(keyframe_data, src_Tpose)

    # get tgt delta rotation TODO: 이 매핑을 구할수있는방법?
    # change order
    tgt_delta_data = copy.deepcopy(src_delta_data)
    tgt_delta_data[0] = src_delta_data[2]
    tgt_delta_data[2] = src_delta_data[0]
    for data_perframe in tgt_delta_data[2]:
        data_perframe *= -1
    # tgt keyframe foramt 
    tgt_keyframe_form = copy.deepcopy(keyframe_data)
    tgt_keyframe_form["rotateX"] = keyframe_data["rotateZ"]
    tgt_keyframe_form["rotateZ"] = keyframe_data["rotateX"]
    
    # get tgt rotation 
    target_data = copy.deepcopy(tgt_delta_data)
    for attr_idx in range(3):
        for fid in range(len(target_data[attr_idx])):
            target_data[attr_idx][fid] = tgt_Tpose[j][attr_idx] # +

    # target의 Tpose 데이터를 알아야
    # print("{} {} {}".format(j, src_joint, tgt_joint))
    set_rotation_keyframe(tgt_joint, target_data, tgt_keyframe_form)

# freeze
incoming_connections = {}
for attr in ['rotateX', 'rotateY', 'rotateZ']:
    full_attr = f"Armature.{attr}"
    connections = cmds.listConnections(full_attr, s=True, d=False, p=True)
    if connections:
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
