import maya.cmds as cmds
import maya.mel as mel
import numpy as np
# import math 
# import copy

def get_joint_hierarchy(root_joint):
    """
    Recursively gets the joint hierarchy starting from the root joint.
    :param root_joint: The root joint to start the hierarchy extraction from.
    :return: A list of joints in the hierarchy.
    """
    hierarchy = []

    def _get_hierarchy(joint):
        children = cmds.listRelatives(joint, children=True, type='joint')
        if children:
            for child in children:
                hierarchy.append(child)
                _get_hierarchy(child)

    hierarchy.append(root_joint)
    _get_hierarchy(root_joint)
    return hierarchy

def get_rotation(node_name):
    if cmds.objExists(node_name):
        rotateX = cmds.getAttr(f"{node_name}.rotateX")
        rotateY = cmds.getAttr(f"{node_name}.rotateY")
        rotateZ = cmds.getAttr(f"{node_name}.rotateZ")
        return rotateX, rotateY, rotateZ
    else:
        return None

def get_rot_matrix(joint_name):
    joint_matrix = cmds.xform(joint_name, q=True, ws=True, m=True) # local coodinaite -> global coordina?
    # print("joint_matrix:", joint_matrix)
    
    # matrix = joint_matrix
    # left_vector = (matrix[0], matrix[1], matrix[2])
    # up_vector = (matrix[4], matrix[5], matrix[6])
    # forward_vector = (matrix[8], matrix[9], matrix[10])
    # print("left_vector:", left_vector)
    # print("up_vector:", up_vector)
    # print("forward_vector:", forward_vector)

    joint_matrix = np.array(joint_matrix)
    joint_matrix = joint_matrix.reshape(4,4)

    return np.transpose(joint_matrix[:3, :3])

# def get_zero_rot_matrix(joint_name):
#     # rotateX = cmds.getAttr(joint_name+".rotateX")
#     # rotateY = cmds.getAttr(joint_name+".rotateY")
#     # rotateZ = cmds.getAttr(joint_name+".rotateZ")
    
#     # set zero and get trf 
#     cmds.setAttr(joint_name+".rotateX", 0)
#     cmds.setAttr(joint_name+".rotateY", 0)
#     cmds.setAttr(joint_name+".rotateZ", 0)
#     zero_rot_trf = get_rot_matrix(joint_name)
#     # zero_rot_trf_copy = copy.deepcopy(zero_rot_trf)
#     # print(type(zero_rot_trf))

#     # back own value
#     # cmds.setAttr(joint_name+".rotateX", rotateX)
#     # cmds.setAttr(joint_name+".rotateY", rotateY)
#     # cmds.setAttr(joint_name+".rotateZ", rotateZ)

#     return zero_rot_trf 

def R_to_E(R):
    # print(R)
    beta = np.arcsin(-R[2, 0])
    
    # Calculate alpha and gamma based on the value of cos(beta)
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

    # return alpha, beta, gamma
    return np.array([alpha, beta, gamma])

def E_to_R(E, order="zyx", radians=True): # 
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
    return np.matmul(np.matmul(R[0], R[1]), R[2])

""" src_to_tgt_map """
if True:
    src_to_tgt_map = {}
    src_to_tgt_map["Hips"] = "Bip001FBXASC032Pelvis"
    src_to_tgt_map["Spine"] = "Bip001FBXASC032Spine"
    src_to_tgt_map["Spine1"] ="Bip001FBXASC032Spine1"
    src_to_tgt_map["Spine2"] ="Bip001FBXASC032Spine2"
    src_to_tgt_map["Neck"] = "Bip001FBXASC032Neck"
    src_to_tgt_map["Neck1"] = "Bip001FBXASC032Head"
    src_to_tgt_map["head"] = "Bip001FBXASC032HeadNub"

    src_to_tgt_map["LeftShoulder"] = "Bip001FBXASC032LFBXASC032Clavicle"
    src_to_tgt_map["LeftArm"]      = "Bip001FBXASC032LFBXASC032UpperArm"
    src_to_tgt_map["LeftForeArm"]  = "Bip001FBXASC032LFBXASC032Forearm"
    src_to_tgt_map["LeftHand"]     = "Bip001FBXASC032LFBXASC032Hand"
    src_to_tgt_map["RightShoulder"]= "Bip001FBXASC032RFBXASC032Clavicle"
    src_to_tgt_map["RightArm"]     = "Bip001FBXASC032RFBXASC032UpperArm"
    src_to_tgt_map["RightForeArm"] = "Bip001FBXASC032RFBXASC032Forearm"
    src_to_tgt_map["RightHand"]    = "Bip001FBXASC032RFBXASC032Hand"

    src_to_tgt_map["LeftUpLeg"]    = "Bip001FBXASC032LFBXASC032Thigh"
    src_to_tgt_map["LeftLeg"]      = "Bip001FBXASC032LFBXASC032Calf"
    src_to_tgt_map["LeftFoot"]     = "Bip001FBXASC032LFBXASC032Foot"
    src_to_tgt_map["LeftToeBase"]  = "Bip001FBXASC032LFBXASC032Toe0"
    src_to_tgt_map["RightUpLeg"]   = "Bip001FBXASC032RFBXASC032Thigh"
    src_to_tgt_map["RightLeg"]     = "Bip001FBXASC032RFBXASC032Calf"
    src_to_tgt_map["RightFoot"]    = "Bip001FBXASC032RFBXASC032Foot"
    src_to_tgt_map["RightToeBase"] = "Bip001FBXASC032RFBXASC032Toe0"


""" src char """
# strDir = "D:/2024_KAI_Retargeting/Adori/SKM_ADORI_0229.fbx"
# mel.eval('FBXImport -f"{}"'.format(strDir))
# cmds.setAttr("ADORI.rotateX", 0) # -90
# cmds.setAttr("Bip001.rotateX", -90) # -90

""" src Tpose """
# Tpose trf 
src_Tpose_trfs = []
src_Tpose_rots = []
object_name = "Hips"
joint_hierarchy = get_joint_hierarchy(object_name)
# for object_name in joint_hierarchy:
# if object_name not in src_to_tgt_map.keys():
#     continue
cmds.currentTime(0)
rot = get_rotation(object_name)
rot = np.array(rot)
rot_mat = get_rot_matrix(object_name)
# rot_mat = np.transpose(rot_mat)
# print("rot:", rot)
# print("rot_mat converted:", E_to_R(rot))
# print("rot_mat:", rot_mat)
src_Tpose_rots.append(rot)
src_Tpose_trfs.append(rot_mat) # transpose E_to_R(rot)

""" src motion """
# get min max time 
if True:
    # src motion by (x key frames, y, z)
    # strDir = "D:/2024_KAI_Retargeting/Adori/animation/0055_Freestyle002_03_RT0214.fbx"
    # mel.eval('FBXImport -f"{}"'.format(strDir))

    # get hierarchy 
    object_name = "Hips"
    joint_hierarchy = get_joint_hierarchy(object_name)

    # Get perjoint_data
    datas = []
    # times 
    min_time = float('inf')
    max_time = float('-inf')

    # get motion
    for object_name in joint_hierarchy:
        perjoint_data = {'rotateX': [], 'rotateY': [], 'rotateZ': [], 
                        'translateX': [], 'translateY': [], 'translateZ': []}
        
        if object_name not in src_to_tgt_map.keys():
            continue
        if object_name=="Hips":
            array = ['rotateX', 'rotateY', 'rotateZ', 'translateX', 'translateY', 'translateZ']
        else:
            array = ['rotateX', 'rotateY', 'rotateZ']
        
        # print(object_name)
        for attr in array:
            keyframe_count = cmds.keyframe(f'{object_name}.{attr}', query=True, keyframeCount=True)
            # print("keyframe_count: ", keyframe_count, object_name, attr)
            if keyframe_count > 0:
                times = cmds.keyframe(f'{object_name}.{attr}', query=True, timeChange=True)
                if attr=="rotateX":
                    times_x = times
                elif attr=="rotateY":
                    times_y = times
                elif attr=="rotateZ":
                    times_z = times
                values = cmds.keyframe(f'{object_name}.{attr}', query=True, valueChange=True)
                
                # times 
                current_min_time = min(times)
                current_max_time = max(times)
                if current_min_time < min_time:
                    min_time = current_min_time
                if current_max_time > max_time:
                    max_time = current_max_time
                perjoint_data[attr] = list(zip(times, values))
        
        datas.append(perjoint_data)

        # times 
        if object_name=="Hips":
            times_x = np.array(times_x)
            times_y = np.array(times_y)
            times_z = np.array(times_z)
            times_x_y = np.union1d(times_x, times_y)
            common_times = np.union1d(times_x_y, times_z) # intersect1d
            # print(common_times)
            # print(len(common_times))

    # source frames 
    cmds.playbackOptions(min=min_time, max=max_time)
    total_frames = int(max_time - min_time + 1)
    # frames = range(0, total_frames)
    # print("Total number of frames:", total_frames)
    # print('times:', times)

# src motions by xform (after set key)
if True:
    src_rots = [] # [frames, joints, 3]
    src_rot_mats = []
    object_name = "Hips"
    joint_hierarchy = get_joint_hierarchy(object_name)
    # for frame in frames: # 이건 정수만 있음.
    for time in common_times:
        cmds.currentTime(time)
        src_frame_rot = []
        src_frame_rot_mat = []
        for object_name in joint_hierarchy:
            if object_name not in src_to_tgt_map.keys():
                continue
            src_rot = get_rotation(object_name) # get_rotation get_rot_matrix
            src_frame_rot.append(src_rot)
            
            rot_mat = get_rot_matrix(object_name)
            # rot_mat = np.transpose(rot_mat)
            src_frame_rot_mat.append(rot_mat)
        src_rots.append(src_frame_rot)
        src_rot_mats.append(src_frame_rot_mat)

""" TGT Tpose """
# Trf 
tgt_Tpose_trfs = []
# Tpose data 
tgt_Tpose_rots = []
object_name = "Bip001FBXASC032Pelvis"
joint_hierarchy = get_joint_hierarchy(object_name)
# for object_name in joint_hierarchy:
# if object_name not in src_to_tgt_map.values():
#     continue
# tgt_front_trf = np.array([[0,1,0],[0,0,1],[1,0,0]]) 
rot = get_rotation(object_name)
rot = np.array(rot)
tgt_Tpose_rots.append(rot)
tgt_Tpose_trfs.append(E_to_R(rot)) # transpose

# Tpose data 
# array = ['rotateX', 'rotateY', 'rotateZ']
# tgt_Tpose_data = []
# for object_name in joint_hierarchy:
#     perjoint_data = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
#     for attr in array:
#         keyframe_count = cmds.keyframe(f'{object_name}.{attr}', query=True, keyframeCount=True)
#         print("tgt keyframe_count: ", keyframe_count, object_name, attr)
#         if keyframe_count > 0:
#             times = cmds.keyframe(f'{object_name}.{attr}', query=True, timeChange=True)
#             values = cmds.keyframe(f'{object_name}.{attr}', query=True, valueChange=True)
#             perjoint_data[attr] = list(zip(times, values))
#     tgt_Tpose_data.append(perjoint_data)
# print("tgt_Tpose_data: ", tgt_Tpose_data)


""" update to target """
# targetDir = "D:/2024_KAI_Retargeting/bear.fbx"
# mel.eval('FBXImport -f"{}"'.format(targetDir))
if True:
    for i, (src_joint, tgt_joint) in enumerate(src_to_tgt_map.items()):
        if i!=0:
            continue

        # set translation 
        perjoint_data = datas[i]
        if i==0:
            array = ["translateX", "translateY", "translateZ",]
            for eid, attr in enumerate(array): 
                value = np.array(perjoint_data[attr])
                for (time, tran) in value: 
                    cmds.setKeyframe(tgt_joint, attribute=attr, t=time, v=tran)
        
        # src
        src_trf = src_Tpose_trfs[i]
        inv_src_trf = np.linalg.inv(src_trf)
        # tgt
        tgt_trf = tgt_Tpose_trfs[i]
        # src to tgt zero trf
        zero_trf = np.array([[0,1,0],[-1,0,0],[0,0,1]])

        if True:
            # set by src_rots (by moving frames)
            array = ['rotateX', 'rotateY', 'rotateZ']
            for tid, time in enumerate(common_times):
                # get src delta rot
                src_rot_mat = np.array(src_rot_mats[tid][i])

                # src
                src_zero_rot_mat = inv_src_trf @ src_rot_mat

                # tgt_zero_rot 
                tgt_zero_rot_mat = zero_trf @ src_zero_rot_mat
                
                # tgt
                tgt_rot_mat = tgt_trf @ tgt_zero_rot_mat
                tgt_rot = R_to_E(tgt_rot_mat)
                if tid==0:
                    src_rot = R_to_E(src_rot_mat)
                    print("src_rot ", src_rot) 
                #     print("src_origin_rot ", src_zero_rot) # must be identity
                #     print("tgt_zero_rot ", tgt_zero_rot) 
                #     print("tgt_rot ", tgt_rot)
                #     print("tgt_rot_angle ", tgt_rot_angle)
                
                for eid, attr in enumerate(array):
                    cmds.setKeyframe(src_joint, attribute=attr, t=time, v=src_rot[eid])
                    cmds.setKeyframe(tgt_joint, attribute=attr, t=time, v=tgt_rot[eid])
                    # print("{} {} {}".format(time, attr, src_rot[eid]))
        
        if False:
            # set by perjoint_data (key frames)
            array = ['rotateX', 'rotateY', 'rotateZ']
            # perjoint_data: (attr, (frames, ros))
            value_x = perjoint_data[array[0]]  
            value_y = perjoint_data[array[1]] 
            value_z = perjoint_data[array[2]] 
            
            # 공통 업데이트 times 찾기
            times_x = []
            for time, _ in value_x:
                times_x.append(time)
            times_y = []
            for time, _ in value_y:
                times_y.append(time)
            times_z = []
            for time, _ in value_z:
                times_z.append(time)
            times_x = np.array(times_x)
            times_y = np.array(times_y)
            times_z = np.array(times_z)
            times_x_y = np.intersect1d(times_x, times_y)
            times = np.intersect1d(times_x_y, times_z)

            # Tpose
            Tpose_rots = np.array([value_x[0][1], value_y[0][1], value_z[0][1]])
            for tid, time in enumerate(times):
                # src rot 
                index_x = np.argwhere(times_x==time)[0][0]
                index_y = np.argwhere(times_y==time)[0][0]
                index_z = np.argwhere(times_z==time)[0][0]
                rots = np.array([value_x[index_x][1], value_y[index_y][1], value_z[index_z][1]])
                src_rots = np.array(rots)

                # delta src, tgt
                src_delta_rots = src_rots # - Tpose_rots np.array([0,90,0]) +
                tgt_delta_rots = np.matmul(trf, src_delta_rots)
                tgt_rots = np.array([0,0,90]) + tgt_delta_rots  # 
                # if tid==(len(times)-1):
                #     print(src_delta_rots)
                #     print(tgt_delta_rots)
                #     print(tgt_rots)
                
                # update 
                for eid, attr in enumerate(array):
                    tgt_rot = tgt_rots[eid]
                    cmds.setKeyframe(tgt_joint, attribute=attr, t=time, v=tgt_rot)
