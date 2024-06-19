import maya.standalone
maya.standalone.initialize(name='python')
import maya.cmds as cmds
import maya.mel as mel
import argparse
import os 
import copy
import numpy as np 
import maya.api.OpenMaya as om
# from scipy.spatial.transform import Rotation as R
# r_z = R.from_euler('z', 90, degrees=True)

"""
usage
- mayapy retargeting_different_axis.py --src_motion_path "" --tgt_char_path "" --tgt_motion_path ""
"""
# D:\_Program\AutoDesk\Maya2023\Maya2023\bin\mayapy retargeting_different_axis.py --sourceMotion "./motions/Adori/animation/0055_Freestyle002_03_RT0214.fbx" --targetChar "./models/Dancstruct/SKM_Asooni_1207.fbx"
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
    for template_joint in template_joints:
        for joint in joints:
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
    form1 = "_bind" # list로 바꾸기
    ret_joints = [] 
    for joint in joints:
        if form in joint or form1 in joint :
            joint = joint.replace(form, "")
        ret_joints.append(joint)
    return ret_joints

def get_keyframe_data(joint):
    # keyframe 
    trans_data = {'translateX': [], 'translateY': [], 'translateZ': []}
    for attr in trans_data.keys():
        keyframe_count = cmds.keyframe(f'{joint}.{attr}', query=True, keyframeCount=True)
        if keyframe_count > 0:
            times = cmds.keyframe(f'{joint}.{attr}', query=True, timeChange=True)
            values = cmds.keyframe(f'{joint}.{attr}', query=True, valueChange=True)
            trans_data[attr] = list(zip(times, values))
            
    # rot 
    rot_data = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
    for attr in rot_data.keys():
        keyframe_count = cmds.keyframe(f'{joint}.{attr}', query=True, keyframeCount=True)
        if keyframe_count > 0:
            times = cmds.keyframe(f'{joint}.{attr}', query=True, timeChange=True)
            values = cmds.keyframe(f'{joint}.{attr}', query=True, valueChange=True)
            rot_data[attr] = list(zip(times, values))
    
    return trans_data, rot_data

def get_array_from_keyframe_data(keyframe_data, rot_attr):
    min_time = 0
    max_time = 0
    for attr in rot_attr:
        data = keyframe_data[attr]
        # last frame
        # print(data)
        time = int(data[-1][0])
        if max_time < time:
            max_time = time
        if min_time > time:
            min_time = time
    rot_data = np.full((max_time+1-min_time, 3), None, dtype=np.float32)
    
    # assume: time이 int 단위
    len_frame = len(rot_data)
    for attr_idx, attr in enumerate(rot_attr.keys()):
        for fid, data_perframe in enumerate(keyframe_data[attr]):
            frame = int(data_perframe[0])
            data = data_perframe[1]
            rot_data[frame, attr_idx] = data
        
        # first frame
        if rot_data[0][attr_idx]==None:
            rot_data[0][attr_idx] = 0
        
        # interpolation TODO: 뒤에 값과 함께 interpolation
        for fid in range(len_frame):
            condition = np.isnan(rot_data[fid][attr_idx])
            if condition:
                rot_data[fid][attr_idx] = rot_data[fid-1][attr_idx]

    return rot_data # [frames, attr 3]

def get_delta_rotation(rot_data):
    src_Tpose = rot_data[0]
    delta_data = rot_data - src_Tpose[None, :]
    
    return delta_data # [attr 3, frames]

def set_translate_keyframe(joint, keyframe_data):
    for attr, keyframes in keyframe_data.items():
        # set only translate
        # if attr=="rotateX" or attr=="rotateY" or attr=="rotateZ":
        #     continue
        for tid, (time, value) in enumerate(keyframes):
            # print("{}: {}".format(time, value))
            cmds.setKeyframe(joint, attribute=attr, time=time, value=value)

def set_keyframe(joint, keyframe_data, rot_attr):
    for attr_idx, attr in enumerate(rot_attr.keys()):
        for tid, perframe_data in enumerate(keyframe_data):
            value = float(perframe_data[attr_idx])
            cmds.setKeyframe(joint, attribute=attr, time=tid, value=value)

def R_to_E_seq(R):
    n = len(R)
    euler_angles = np.zeros((n, 3))
    for i in range(n):
        euler_angles[i] = R_to_E(R[i])

    return euler_angles

def R_to_E(R):
    beta = np.arcsin(-R[2, 0]) # beta (y axis)
    
    # Calculate alpha(z axis) and gamma (x axis) based on the value of cos(beta)
    if np.cos(beta) != 0:
        alpha = np.arctan2(R[2, 1], R[2, 2])
        gamma = np.arctan2(R[1, 0], R[0, 0])
    else:
        alpha = np.arctan2(-R[1, 2], R[1, 1])
        gamma = 0

    # Convert radians to degrees
    alpha = np.degrees(alpha)
    beta = np.degrees(beta)
    gamma = np.degrees(gamma)

    return np.array([alpha, beta, gamma])

def E_to_R(E, order="zyx", radians=False):
    """
    Args:
        E: (..., 3)
    """
    if E.shape[-1] != 3:
        raise ValueError(f"Invalid Euler angles shape {E.shape}")
    if len(order) != 3:
        raise ValueError(f"Order must have 3 characters, but got {order}")

    if not radians:
        E = np.deg2rad(E)

    def _euler_axis_to_R(angle, axis):
        one  = np.ones_like(angle, dtype=np.float32)
        zero = np.zeros_like(angle, dtype=np.float32)
        cos  = np.cos(angle, dtype=np.float32)
        sin  = np.sin(angle, dtype=np.float32)

        if axis == "x":
            R_flat = (one, zero, zero, zero, cos, -sin, zero, sin, cos)
        elif axis == "y":
            R_flat = (cos, zero, sin, zero, one, zero, -sin, zero, cos)
        elif axis == "z":
            R_flat = (cos, -sin, zero, sin, cos, zero, zero, zero, one)
        else:
            raise ValueError(f"Invalid axis: {axis}")
        return np.stack(R_flat, axis=-1).reshape(angle.shape + (3, 3))

    R = [_euler_axis_to_R(E[..., i], order[i]) for i in range(3)]
    
    # order=="zyx" 
    # R = np.matmul(R[2], np.matmul(R[1], R[0]))
    R = np.matmul(np.matmul(R[0], R[1]), R[2])
    
    return R

def get_parser():
    parser = argparse.ArgumentParser(description='Import an FBX file into Maya')
    parser.add_argument('--sourceMotion', type=str, default="./motions/Adori/animation/0055_Freestyle002_03_RT0214.fbx")
    parser.add_argument('--targetChar', type=str, default="./models/Dancstruct/SKM_ADORI_0229.fbx")
    parser.add_argument('--tgt_motion_path', type=str, default="./output/")
    return parser

def get_args():
    parser = get_parser()
    return parser.parse_args()

# get src delta rotation (assumption: first frame is Tpose)
def get_rot_mat(src_joint, bool_worldSpace):
    tgt_Tpose_rot = cmds.xform(src_joint, query=True, worldSpace=bool_worldSpace, rotation=True)
    tgt_Tpose_rot = np.array(tgt_Tpose_rot)
    tgt_Tpose_rot = E_to_R(tgt_Tpose_rot)
    return tgt_Tpose_rot

# dict
# Asooni src 
src_template_joints = \
    ["Hips","Spine","Spine1","Spine2", # 4
     "Neck","Head", #"HeadTop_End", # 2
     "LeftShoulder","LeftArm","LeftForeArm","LeftHand", # 4
     "RightShoulder","RightArm","RightForeArm","RightHand", # 4
     "LeftUpLeg","LeftLeg","LeftFoot","LeftToeBase", #"LeftToe_End", # 4
     "RightUpLeg","RightLeg","RightFoot","RightToeBase"] # , "RightToe_End"  # 4
    # 22

# adori
tgt_template_joints = \
    ['Hips', 'Spine', 'Spine1', 'Spine2', #'Spine3', 'Spine4',  # 4
     'Neck', "Head", # 2 'Neck1', 
     'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand',  # 4
     'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand', # 4
     'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase', # 4
     'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase'] # 4
    # 22

def main():
    # Load the FBX plugin
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        cmds.loadPlugin('fbxmaya')

    args = get_args()

    """ tgt character """
    targetChar = args.targetChar
    mel.eval('FBXImport -f"{}"'.format(targetChar))
    target_char = targetChar.split('/')[-1].split('.')[0]
    # tgt joint hierarchy
    tgt_joints = cmds.ls(type='joint')
    root_joint = find_root_joints(tgt_joints)
    tgt_joint_hierarchy = get_joint_hierarchy(root_joint)
    tgt_joint_hierarchy = refine_joints(tgt_joint_hierarchy, tgt_template_joints)
    # get locator rotation 
    tgt_locator = cmds.ls(type='locator')
    tgt_locator = tgt_locator[0].replace("Shape","")

    # Tpose of tgt (inital pose for updating delta)
    tgt_Tpose = [[0,0,0] for _ in range(len(tgt_joint_hierarchy))] # [num_joint, attr 3]
    # other joint: tgt load할때 얻기
    for i, joint in enumerate(tgt_joint_hierarchy):
        tgt_Tpose[i] = cmds.xform(joint, q=True, ws=False, ro=True)
    tgt_Tpose = np.array(tgt_Tpose)


    """ src motion """
    sourceMotion = args.sourceMotion
    mel.eval('FBXImport -f"{}"'.format(sourceMotion))
    target_motion = sourceMotion.split('/')[-1].split('.')[0]

    # src locator 
    src_locator = cmds.ls(type='locator')
    src_locator = list(set(src_locator) - set(tgt_locator))
    src_locator = src_locator[0].replace("Shape","")
    src_locator_translation = cmds.xform(src_locator, q=True, ws=True, ro=True)
    print("{} src_locator_translation {}".format(src_locator, src_locator_translation))
    # hip joint: inverse of locator rotation 
    for i in range(3):
        tgt_Tpose[0][i] = -src_locator_translation[i]

    # refine joint hierarchy
    src_joints = cmds.ls(type='joint')
    src_joints = list(set(src_joints) - set(tgt_joints))
    root_joint = find_root_joints(src_joints)
    src_joint_hierarchy = get_joint_hierarchy(root_joint)
    src_joint_hierarchy = refine_joints(src_joint_hierarchy, src_template_joints)

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

    src_select_hierarchy, tgt_select_hierarchy = [], []
    for i in range(len(src_joint_index)):
        src_select_hierarchy.append(src_joint_hierarchy[src_joint_index[i]])
        tgt_select_hierarchy.append(tgt_joint_hierarchy[tgt_joint_index[i]])
    src_joint_hierarchy = src_select_hierarchy
    tgt_joint_hierarchy = tgt_select_hierarchy


    """ retarget """
    # locator
    cmds.xform(tgt_locator, ws=False, ro=src_locator_translation)

    # joints
    for j, (src_joint, tgt_joint) in enumerate(zip(src_joint_hierarchy, tgt_joint_hierarchy)):
        if j!=0:
            continue

        # keyframe_data [attr, frames, (frame, value)]
        trans_data, keyframe_data = get_keyframe_data(src_joint)
        
        # root translation
        if j==0:
            trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
            trans_data = get_array_from_keyframe_data(trans_data, trans_attr)
            set_keyframe(tgt_joint, trans_data, trans_attr)
        
        """ trf """
        # src data 
        rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
        rot_data = get_array_from_keyframe_data(keyframe_data, rot_attr)
        src_rot_mat = E_to_R(rot_data)
        src_Tpose_rot = src_rot_mat[0]

        # tgt Tpose
        tgt_Tpose_rot = get_rot_mat(tgt_joint, False)
        if j==0:
            # rotate (x 90)
            tgt_Tpose_rot = np.array([[1,0,0],[0,0,-1],[0,1,0]]) @ tgt_Tpose_rot

        # trf for Tpose
        trf = tgt_Tpose_rot @ np.linalg.inv(src_Tpose_rot)
        len_frame = rot_data.shape[0]
        trf = trf[None, ...].repeat(len_frame, axis=0)

        # update tgt 
        tgt_rot_mat = trf @ src_rot_mat
        target_data = R_to_E_seq(tgt_rot_mat)

        # joint rotation
        set_keyframe(tgt_joint, target_data, rot_attr)


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

if __name__=="__main__":
    main()