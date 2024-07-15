import maya.standalone
maya.standalone.initialize(name='python')
import maya.cmds as cmds
import maya.mel as mel
import argparse
import os 
import copy
import numpy as np 
import maya.api.OpenMaya as om

"""
usage
- mayapy retargeting_different_axis.py --src_motion_path "" --tgt_char_path ""

Window 
D:\_Program\AutoDesk\Maya2023\Maya2023\bin\mayapy retargeting_different_axis.py 
--sourceMotion "./motions/Asooni/animation_before_edit/Go Hard - TWICE_002_RT0118.fbx" 
--targetChar "./models/Dancstruct/SKM_ADORI_0229.fbx"

Mac 
/Applications/Autodesk/maya2025/Maya.app/Contents/MacOS/mayapy retargeting_different_axis.py 
--sourceMotion './motions/Asooni/animation_before_edit/Go Hard - TWICE_002_RT0118.fbx' 
--targetChar './models/Dancstruct/SKM_ADORI_0229.fbx'
"""

# joints
template_joints = [
    "Hips","Spine","Spine1","Spine2",
     "Neck","Head", 
     "LeftShoulder","LeftArm","LeftForeArm","LeftHand", 
     "RightShoulder","RightArm","RightForeArm","RightHand", 
     "LeftUpLeg","LeftLeg","LeftFoot","LeftToeBase",
     "RightUpLeg","RightLeg","RightFoot","RightToeBase"]
    # 22 = 4+2+4+4+4+4

alter_joint_name = {
     "Hips":["Pelvis", "LowerTorso"], 
     "Spine":["UpperTorso",],

     "LeftShoulder": ["LFBXASC032Clavicle", "LeftUpperArm"], 
     "LeftArm":["LFBXASC032UpperArm", "LeftLowerArm"], 
     "LeftForeArm":["LFBXASC032Forearm"], 
     "LeftHand": ["LFBXASC032Hand"],

     "RightShoulder":["RFBXASC032Clavicle", "RightUpperArm"], 
     "RightArm":["RFBXASC032UpperArm", "LeftUpperArm"], 
     "RightForeArm":["RFBXASC032Forearm"], 
     "RightHand":["RFBXASC032Hand"], 

     "LeftUpLeg":['LFBXASC032Thigh'], 
     "LeftLeg":['LFBXASC032Calf'], 
     "LeftFoot":['LFBXASC032Foot'], 
     "LeftToeBase":['LFBXASC032Toe0'], 

     "RightUpLeg":['RFBXASC032Thigh'], 
     "RightLeg":['RFBXASC032Calf'], 
     "RightFoot":['RFBXASC032Foot'], 
     "RightToeBase":['RFBXASC032Toe0'], 
    }

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

def select_joints(joints, template_joints):
    refined_joints = []
    for template_joint in template_joints:
        for joint in joints:
            # find alternative name 
            alter_joint = joint
            for temp_name, alter_names in alter_joint_name.items():
                changed = False
                for alter_name in alter_names:
                    if joint in alter_name or alter_name in joint:
                        alter_joint = temp_name
                        changed = True
                        break
                if changed:
                    break

            # joint in template joint, not finger  
            if (template_joint.lower() in joint.lower() or joint.lower() in template_joint.lower() or \
                template_joint.lower() in alter_joint.lower() or alter_joint.lower() in template_joint.lower()) and \
                "Thumb" not in joint and \
                "Index" not in joint and \
                "Middle" not in joint and \
                "Ring" not in joint and \
                "Pinky" not in joint:
                refined_joints.append(joint)
                break
        
    return refined_joints

def refine_joint_name(joints):
    ret_joints = [] 
    for joint in joints:
        # replace joint name as template name
        for temp_joint, alter_joints in alter_joint_name.items():
            for alter_joint in alter_joints:
                if joint in alter_joint or alter_joint in joint:
                    joint = temp_joint
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
    # first_data = np.array([None, None, None])
    for attr_idx, attr in enumerate(rot_attr.keys()):
        data = keyframe_data[attr]
        
        # time 
        if len(data)==0:
            print("no data for", attr)
            continue
        time = int(data[-1][0])
        if max_time < time:
            max_time = time
        if min_time > time:
            min_time = time
    rot_data = np.full((max_time+1-min_time, 3), None, dtype=np.float32)
    
    len_frame = len(rot_data)
    for attr_idx, attr in enumerate(rot_attr.keys()):
        for fid, data_perframe in enumerate(keyframe_data[attr]):
            frame = int(data_perframe[0])
            data = data_perframe[1]
            rot_data[frame, attr_idx] = data
        
        # if first first is nan
        if np.isnan(rot_data[0][attr_idx]):
            len_frame = len(rot_data)
            for i in range(len_frame):
                if np.isnan(rot_data[i][attr_idx])==False:
                    rot_data[0][attr_idx] = rot_data[i][attr_idx]
                    break
        
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
            cmds.setKeyframe(joint, attribute=attr, time=time, value=value)

def set_keyframe(joint, keyframe_data, rot_attr):
    for attr_idx, attr in enumerate(rot_attr.keys()):
        for tid, perframe_data in enumerate(keyframe_data):
            value = float(perframe_data[attr_idx])
            cmds.setKeyframe(joint, attribute=attr, time=tid, value=value) # world 로 가능?

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
 
def E_to_R(E, order="xyz", radians=False): # order: rotation값이 들어오는 순서
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

    # rotation multiplication order: ZYX (Rz * Ry * Rx)
    R = np.matmul(np.matmul(R[2], R[1]), R[0])
    
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

def get_world_rot_data(joint_name):
    # Get rotation keyframe data
    rot_data = cmds.keyframe(joint_name, query=True, attribute='rotate', valueChange=True, timeChange=True)
    
    # Organize the data into arrays
    rot_data_array = np.array(rot_data).reshape(-1, 2) # 6038 -> [3*3018, 2] 
    max_time = int(np.max(rot_data_array[:, 0]))
    min_time = 0
    
    rot_data = np.full((max_time+1-min_time, 3), None, dtype=np.float32)
    attr_idx = 0
    prev_time = -1
    for data in rot_data_array:
        time = int(data[0])
        rot = data[1]
        if prev_time > time:
            attr_idx += 1
        rot_data[time, attr_idx] = rot 
        prev_time = time

    # interpolation
    len_frame = len(rot_data)
    for attr_idx in range(3):
        # if first first is nan
        if np.isnan(rot_data[0][attr_idx]):
            for f in range(len_frame):
                if np.isnan(rot_data[f][attr_idx])==False:
                    rot_data[0][attr_idx] = rot_data[f][attr_idx]
                    break

        # interpolation 
        for fid in range(len_frame):
            condition = np.isnan(rot_data[fid][attr_idx])
            if condition:
                rot_data[fid][attr_idx] = rot_data[fid-1][attr_idx]

    return rot_data

import math
def get_world_vector_from_world_rot(rot_data, vector): # world rot, vector
    vector = np.array(vector)

    forward_vectors = []
    for i, frame_rot in enumerate(rot_data):
        frame_rot = [math.radians(angle) for angle in frame_rot]

        rotation = om.MEulerRotation(om.MVector(frame_rot[0], frame_rot[1], frame_rot[2]), om.MEulerRotation.kXYZ) # TODO
        transform_matrix = om.MTransformationMatrix()
        transform_matrix.setRotation(rotation.asQuaternion())
        transform_matrix = np.array(transform_matrix.asMatrix()).reshape(4,4)[:3, :3]
        transform_matrix = np.transpose(transform_matrix) # Transpose 

        # Get the forward vector (positive Z axis in local space)
        forward_vector = vector @ transform_matrix
        forward_vectors.append(forward_vector)

    return np.array(forward_vectors)

def get_parent_joint(joint):
    parent = cmds.listRelatives(joint, parent=True)
    if parent:
        return parent[0]
    else:
        return None
    
def get_top_level_nodes():
    return cmds.ls(assemblies=True)

def main():
    # Load the FBX plugin
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        cmds.loadPlugin('fbxmaya')

    args = get_args()

    """ tgt character """
    if True:
        targetChar = args.targetChar
        mel.eval('FBXImport -f"{}"'.format(targetChar))
        target_char = targetChar.split('/')[-1].split('.')[0]
        # tgt joint hierarchy
        tgt_joints = cmds.ls(type='joint')
        tgt_root_joint = find_root_joints(tgt_joints)
        tgt_joint_hierarchy = get_joint_hierarchy(tgt_root_joint)
        tgt_joint_hierarchy = select_joints(tgt_joint_hierarchy, template_joints)

        # Tpose of tgt (inital pose for updating delta)
        tgt_Tpose = [[0,0,0] for _ in range(len(tgt_joint_hierarchy))] # [num_joint, attr 3]
        # other joint: tgt load할때 얻기
        for i, joint in enumerate(tgt_joint_hierarchy):
            tgt_Tpose[i] = cmds.xform(joint, q=True, ws=False, ro=True)
        tgt_Tpose = np.array(tgt_Tpose)

        # get locator rotation 
        tgt_locator = cmds.ls(type='locator')
        if len(tgt_locator)!=0:
            tgt_locator = tgt_locator[0].replace("Shape","")
            tgt_locator_rot = cmds.xform(tgt_locator, q=True, ws=True, ro=True)
            tgt_locator_pos = cmds.xform(tgt_locator, q=True, ws=True, translation=True)
            # tgt_locator_pos[0] = 200 # translate
            cmds.xform(tgt_locator, q=False, ws=True, translation=tgt_locator_pos)

    """ joint hierarchy """
    if True:
        # nodes_before_import = set(get_top_level_nodes())

        # import Tpose
        sourceMotion = args.sourceMotion
        sourceChar = sourceMotion.split('/')[2]
        Tpose = "./motions/"+sourceChar+"/animation_before_edit/T-Pose.fbx"
        mel.eval('FBXImport -f"{}"'.format(Tpose))

        # refine joint hierarchy
        src_joints = cmds.ls(type='joint')
        src_joints = list(set(src_joints) - set(tgt_joints))
        root_joint = find_root_joints(src_joints)
        src_joint_hierarchy = get_joint_hierarchy(root_joint)
        src_joint_hierarchy = select_joints(src_joint_hierarchy, template_joints)

        # find common joints 
        src_common_joint = []
        tgt_common_joint = []
        tgt_joint_hierarchy_refined = refine_joint_name(tgt_joint_hierarchy)
        print(tgt_joint_hierarchy)
        print("tgt: ", tgt_joint_hierarchy_refined)
        print("src: ", src_joint_hierarchy)
        for src_joint in src_joint_hierarchy:
            check = False
            for tgt_joint in tgt_joint_hierarchy_refined:
                # src_joint_ori = copy.deepcopy(src_joint)
                # tgt_joint_ori = copy.deepcopy(tgt_joint)

                # find common joint 
                if src_joint.lower() in tgt_joint.lower() or tgt_joint.lower() in src_joint.lower():
                    src_common_joint.append(src_joint) # _ori
                    tgt_common_joint.append(tgt_joint) # _ori
                    check = True 
                    break
            if check:
                continue
        print(src_common_joint)
        print(tgt_common_joint)

        # joint index 
        src_joint_index, tgt_joint_index = [], []
        for joint in src_common_joint:
            src_joint_index.append(src_joint_hierarchy.index(joint))
        for joint in tgt_common_joint:
            tgt_joint_index.append(tgt_joint_hierarchy_refined.index(joint))

        # selected joint hierarchy
        src_select_hierarchy, tgt_select_hierarchy = [], []
        for i in range(len(src_joint_index)):
            src_select_hierarchy.append(src_joint_hierarchy[src_joint_index[i]])
            tgt_select_hierarchy.append(tgt_joint_hierarchy[tgt_joint_index[i]])
        src_joint_hierarchy = src_select_hierarchy
        tgt_joint_hierarchy = tgt_select_hierarchy
    # print(tgt_joint_hierarchy)
        
        # remove Tpose motion
        # nodes_after_import = set(get_top_level_nodes())
        # imported_nodes = nodes_after_import - nodes_before_import
        # Delete the imported nodes
        # print(imported_nodes)
        # if imported_nodes:
        #     cmds.delete(imported_nodes)

    """ Tpose """
    if True:
        Tpose_trfs = []
        for j, (src_joint, tgt_joint) in enumerate(zip(src_joint_hierarchy, tgt_joint_hierarchy)):
            # world 
            # src 
            src_rot_data = np.transpose(np.array(cmds.xform(src_joint, q=True, ws=True, matrix=True)).reshape(4,4)[:3,:3]) # ws=False
            # tgt 
            tgt_rot_data = np.transpose(np.array(cmds.xform(tgt_joint, q=True, ws=True, matrix=True)).reshape(4,4)[:3,:3])
            # trf 
            trf = np.linalg.inv(src_rot_data) @ tgt_rot_data
            Tpose_trfs.append(trf)
    
    """ import src motion """
    if True:
        sourceMotion = args.sourceMotion
        mel.eval('FBXImport -f"{}"'.format(sourceMotion))
        target_motion = sourceMotion.split('/')[-1].split('.')[0]

        # src locator 
        src_locator = cmds.ls(type='locator')
        if len(tgt_locator) != 0:
            src_locator = list(set(src_locator) - set(tgt_locator))
        else:
            src_locator = list(set(src_locator))
        src_locator = src_locator[0].replace("Shape","")
        src_locator_translation = cmds.xform(src_locator, q=True, ws=True, ro=True)

        # hip joint: inverse of locator rotation 
        for i in range(3):
            tgt_Tpose[0][i] = -src_locator_translation[i]

    """ retarget """
    # locator
    # cmds.xform(tgt_locator, ws=False, ro=src_locator_translation)

    # target position
    for j, (src_joint, tgt_joint) in enumerate(zip(src_joint_hierarchy, tgt_joint_hierarchy)):
        """ src """
        # keyframe_data [attr, frames, (frame, value)]
        trans_data, rot_data = get_keyframe_data(src_joint) # world 

        # Tpose difference
        # source_mat = Tpose_rots[j] #np.transpose(np.array().reshape(4,4))[:3,:3] # E_to_R
        # target_mat = np.transpose(np.array(cmds.xform(tgt_joint, q=True, ws=True, matrix=True)).reshape(4,4))[:3,:3]
        # Tpose_diff = np.linalg.inv(source_mat) @ target_mat

        """ translation """
        if j==0:
            trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
            trans_data = get_array_from_keyframe_data(trans_data, trans_attr)
            len_frame = len(trans_data)
            if len_frame!=0:
                if len(tgt_locator)!=0:
                    tgt_locator_rot_mat = E_to_R(-1 * np.array(tgt_locator_rot))
                else:
                    tgt_locator_rot_mat = np.identity()
                tgt_trans_data = np.einsum('ijk,ik->ij', tgt_locator_rot_mat[None, :].repeat(len_frame, axis=0), trans_data)
                # update position
                set_keyframe(tgt_joint, tgt_trans_data, trans_attr)

        """ tgt target angle from src """
        # src: world rotation for tgt
        rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
        rot_data = get_array_from_keyframe_data(rot_data, rot_attr)

        """ update data """
        max_time = len(rot_data)
        min_time = 0
        desired_rot_data = np.full((max_time+1-min_time, 3), None, dtype=np.float32)
        for i in range(len_frame):
            """ src """
            # src world angle
            src_local_angle = rot_data[i]
            src_local_mat = E_to_R(src_local_angle)
            
            # src parent angle 
            if j==0:
                # locator
                src_parent_rot_mat = E_to_R(np.array([0,0,0])) # src_locator_rot TODO: src가 다를때 확인 
            else:
                # tgt parent world rot
                src_parent_joint = get_parent_joint(src_joint)
                src_parent_rot_mat = np.transpose(np.array(cmds.xform(src_parent_joint, q=True, ws=True, matrix=True)).reshape(4,4))[:3,:3]
            src_world_mat = src_parent_rot_mat @ src_local_mat

            # target world angle 
            tgt_world_mat = src_world_mat @ Tpose_trfs[j]

            # update by frame
            if j==0:
                # locator
                tgt_parent_rot_mat = E_to_R(np.array(tgt_locator_rot))
            else:
                # tgt parent world rot
                tgt_parent_joint = get_parent_joint(tgt_joint)
                tgt_parent_rot_mat = np.transpose(np.array(cmds.xform(tgt_parent_joint, q=True, ws=True, matrix=True)).reshape(4,4))[:3,:3] 
            tgt_local_mat = np.linalg.inv(tgt_parent_rot_mat) @ tgt_world_mat
            tgt_local_angle = R_to_E(tgt_local_mat)
            desired_rot_data[i] = tgt_local_angle

        # update by joint
        set_keyframe(tgt_joint, desired_rot_data, rot_attr)

    # freeze
    incoming_connections = {}
    if len(tgt_locator)!=0:
        top_joint = tgt_locator
    else:
        top_joint = tgt_root_joint
    for attr in ['rotateX', 'rotateY', 'rotateZ']:
        # top joint 
        full_attr = f"{top_joint}.{attr}"
        connections = cmds.listConnections(full_attr, s=True, d=False, p=True)
        if connections:
            incoming_connections[attr] = connections[0]
            cmds.disconnectAttr(connections[0], full_attr)
    # bake
    cmds.bakeResults("{}".format(top_joint), simulation=True, t=(cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True)), sampleBy=1, oversamplingRate=1, disableImplicitControl=True, preserveOutsideKeys=True, sparseAnimCurveBake=False, removeBakedAnimFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=False, shape=True)

    # export 
    output_dir = args.tgt_motion_path + target_char
    os.makedirs(output_dir, exist_ok=True)
    export_file = output_dir+'/'+target_motion+'.fbx'
    mel.eval('FBXExport -f"{}"'.format(export_file))
    maya.standalone.uninitialize()
    print("File export to ", export_file)

if __name__=="__main__":
    main()