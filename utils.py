import maya.standalone
maya.standalone.initialize(name='python')
import maya.cmds as cmds
import maya.mel as mel
import argparse
import os 
import copy
import numpy as np 
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import traceback
import math
import argparse

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

def get_parser():
    parser = argparse.ArgumentParser(description='Import an FBX file into Maya')
    parser.add_argument('--Tpose_char', type=str, default="")
    return parser

def get_args():
    parser = get_parser()
    return parser.parse_args()

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

def get_meshes():
    meshes = cmds.ls(type='mesh')
    return meshes

def get_vertex_positions(mesh):
    vertices = cmds.ls(f'{mesh}.vtx[*]', fl=True)
    positions = [cmds.pointPosition(vertex) for vertex in vertices]
    return positions

def get_normals(mesh):
    selection_list = om.MSelectionList()
    selection_list.add(mesh)
    dag_path = selection_list.getDagPath(0)
    mesh_fn = om.MFnMesh(dag_path)
    
    normals = []
    for i in range(mesh_fn.numVertices):
        normal = mesh_fn.getVertexNormal(i, om.MSpace.kWorld)
        normals.append((normal.x, normal.y, normal.z))
    return normal

def get_frame_range_mesh_data(mesh, start_frame, end_frame):
    Data = []
    for frame in range(start_frame, end_frame+1) :
        cmds.currentTime(frame, edit=True)
        positions = get_vertex_positions(mesh)
        Data.append(positions)
    return np.array(Data)

def get_frame_range_joint_data(joint, start_frame, end_frame):
    Data = []
    for frame in range(start_frame, end_frame+1) :
        cmds.currentTime(frame, edit=True)
        positions = cmds.xform(joint, query=True, worldSpace=True, translation=True)
        rotations = cmds.xform(joint, query=True, worldSpace=True, rotation=True)
        comb = positions + rotations
        Data.append(comb)
    return np.array(Data)


def get_skin_weights(mesh_name):
    # 선택한 메시의 skinCluster 찾기
    skin_cluster_name = None
    history = cmds.listHistory(mesh_name)
    skin_clusters = cmds.ls(history, type='skinCluster')
    
    if skin_clusters:
        skin_cluster_name = skin_clusters[0]
    else:
        raise RuntimeError(f"No skinCluster found for mesh: {mesh_name}")
    
    # SkinCluster의 MObject 가져오기
    selection_list = om.MSelectionList()
    selection_list.add(skin_cluster_name)
    skin_cluster_mobject = selection_list.getDependNode(0)
    skin_cluster_fn = oma.MFnSkinCluster(skin_cluster_mobject)
    
    # 메시의 MObject 가져오기
    selection_list.clear()
    selection_list.add(mesh_name)
    dag_path = selection_list.getDagPath(0)
    
    # 스킨 클러스터에 바인딩된 버텍스 가져오기
    vertex_iter = om.MItGeometry(dag_path)
    
    # 스킨 클러스터의 인플루언스들 가져오기
    inf_dag_paths = skin_cluster_fn.influenceObjects()
    
    # 각 인플루언스별로 가중치 가져오기
    weights = []
    joint_names = [cmds.ls(influence.fullPathName(), long=False)[0] for influence in inf_dag_paths]

    # 각 버텍스에 대해 가중치 추출
    while not vertex_iter.isDone():
        weight_values = skin_cluster_fn.getWeights(dag_path, vertex_iter.currentItem())
        
        # weight_values를 넘파이 배열로 변환하여 weights 리스트에 추가
        weights.append(np.array(weight_values))

        vertex_iter.next()
    
    # 가중치 리스트를 넘파이 2차원 배열로 변환
    return weights, joint_names

'''
def get_frame_range_joint_rot_data(joint, start_frame, end_frame):
    Data = []
    for frame in range(start_frame, end_frame+1) :
        cmds.currentTime(frame, edit=True)

    
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
'''