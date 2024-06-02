import maya.cmds as cmds
import maya.mel as mel
# import math 
import numpy as np
import copy

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
    return joint_matrix[:3, :3] # copy.deepcopy

def get_zero_rot_matrix(joint_name):
    # rotateX = cmds.getAttr(joint_name+".rotateX")
    # rotateY = cmds.getAttr(joint_name+".rotateY")
    # rotateZ = cmds.getAttr(joint_name+".rotateZ")
    
    # set zero and get trf 
    cmds.setAttr(joint_name+".rotateX", 0)
    cmds.setAttr(joint_name+".rotateY", 0)
    cmds.setAttr(joint_name+".rotateZ", 0)
    zero_rot_trf = get_rot_matrix(joint_name)
    # zero_rot_trf_copy = copy.deepcopy(zero_rot_trf)
    # print(type(zero_rot_trf))

    # back own value
    # cmds.setAttr(joint_name+".rotateX", rotateX)
    # cmds.setAttr(joint_name+".rotateY", rotateY)
    # cmds.setAttr(joint_name+".rotateZ", rotateZ)

    return zero_rot_trf 

def R_to_E(R):
    
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

""" src """
# Tpose trf 
src_Tpose_trfs = [] # check changed 
src_Tpose_rots = []
object_name = "Hips"
joint_hierarchy = get_joint_hierarchy(object_name)
# for object_name in joint_hierarchy:
# if object_name not in src_to_tgt_map.keys():
#     continue
cmds.currentTime(0)
src_Tpose_trfs.append(get_rot_matrix(object_name)) # copy.deepcopy(
src_Tpose_rots.append(get_rotation(object_name))
# print("src_Tpose_trfs: ", src_Tpose_trfs)
# print("src_Tpose_rots: ", src_Tpose_rots)


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
            print(common_times)
            print(len(common_times))


    # source frames 
    cmds.playbackOptions(min=min_time, max=max_time)
    total_frames = int(max_time - min_time + 1)
    # frames = range(0, total_frames)
    # print("Total number of frames:", total_frames)
    # print('times:', times)

# src motions by xform (after set key)
if True:
    src_rots = [] # [frames, joints, 3]
    object_name = "Hips"
    joint_hierarchy = get_joint_hierarchy(object_name)
    # for frame in frames: # 이건 정수만 있음.
    for time in common_times:
        cmds.currentTime(time)
        src_frame_rot = []
        for object_name in joint_hierarchy:
            if object_name not in src_to_tgt_map.keys():
                continue
            src_rot = get_rot_matrix(object_name)
            src_frame_rot.append(src_rot)
        src_rots.append(src_frame_rot)

""" TGT """
# Trf 
tgt_Tpose_trfs = []
# Tpose data 
tgt_Tpose_rots = []
object_name = "Bip001FBXASC032Pelvis"
joint_hierarchy = get_joint_hierarchy(object_name)
# for object_name in joint_hierarchy:
# if object_name not in src_to_tgt_map.values():
#     continue
tgt_Tpose_trfs.append(get_rot_matrix(object_name))
tgt_Tpose_rots.append(get_rotation(object_name))
# print("{}: {}".format(object_name, tgt_Tpose_rot))
# print("tgt_Tpose_trfs:", tgt_Tpose_trfs)
# print("tgt_Tpose_rots:", tgt_Tpose_rots)

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
        
        # src zero trf 
        # src_Tpose_trf = src_Tpose_trfs[i] # np.transpose(
        # print("src_Tpose_trf:", src_Tpose_trf)
        # inv_src_Tpose_trf = np.linalg.inv(src_Tpose_trf)
        # print("inv_src_Tpose_trf:", inv_src_Tpose_trf)
        # update to tgt
        # tgt_Tpose_trf = tgt_Tpose_trfs[i] # np.transpose
        # print("tgt_Tpose_trf:", tgt_Tpose_trf)
        # trf 
        # trf = np.matmul(tgt_Tpose_trf, inv_src_Tpose_trf)
        # trf = np.matmul(inv_src_Tpose_trf, tgt_Tpose_trf)
        # trf = np.array([[1,0,0], [0,0,-1], [0,1,0]])
        trf = np.array([[0,-1,0], [1,0,0], [0,0,1]])
        # trf = np.array([[0,-1,0], [0,0,1], [1,0,0]])
        # trf = np.array([[0,0,1], [0,1,0], [-1,0,0]])
        trf = np.transpose(trf)

        if True:
            # set by src_rots (by moving frames)
            array = ['rotateX', 'rotateY', 'rotateZ']
            # Tpose rot 
            # src_Tpose_rot = np.array(src_Tpose_rots[i])
            # tgt_Tpose_rot = np.array(tgt_Tpose_rots[i])
            for tid, time in enumerate(common_times):
                # get src delta rot
                src_rot = np.array(src_rots[tid][i])
                # print("{}: {}".format(time, src_rot))
                # src_delta_rot = rots - src_Tpose_rot

                # set tgt rot
                # tgt_delta_rot = np.matmul(tgt_zero_trf, np.matmul(inv_src_zero_trf, src_delta_rot))
                # tgt_rot = tgt_Tpose_rot + tgt_delta_rot
                # tgt_rot = np.matmul(tgt_zero_trf, np.matmul(inv_src_zero_trf, rots)) 
                
                # delta src, tgt
                src_delta_rot = src_rot # - Tpose_rots np.array([0,90,0]) +
                tgt_delta_rot = np.matmul(trf, src_delta_rot)
                # print(tgt_delta_rot)
                tgt_delta_rot = R_to_E(tgt_delta_rot)

                tgt_rot = tgt_delta_rot
                
                for eid, attr in enumerate(array):
                    cmds.setKeyframe(tgt_joint, attribute=attr, t=time, v=tgt_rot[eid])
        
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
