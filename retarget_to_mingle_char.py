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
    joint_matrix = np.array(joint_matrix)
    joint_matrix = joint_matrix.reshape(4,4)
    return (joint_matrix[:3, :3]) # copy.deepcopy

def get_zero_rot_matrix(joint_name):
    # rotateX = cmds.getAttr(joint_name+".rotateX")
    # rotateY = cmds.getAttr(joint_name+".rotateY")
    # rotateZ = cmds.getAttr(joint_name+".rotateZ")
    
    # set zero and get trf 
    cmds.setAttr(joint_name+".rotateX", 0)
    cmds.setAttr(joint_name+".rotateY", 0)
    cmds.setAttr(joint_name+".rotateZ", 0)
    zero_rot_trf = get_rot_matrix(joint_name)
    zero_rot_trf_copy = copy.deepcopy(zero_rot_trf)
    # print(type(zero_rot_trf))

    # back own value
    # cmds.setAttr(joint_name+".rotateX", rotateX)
    # cmds.setAttr(joint_name+".rotateY", rotateY)
    # cmds.setAttr(joint_name+".rotateZ", rotateZ)

    return zero_rot_trf_copy 

# src_to_tgt_map
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
# src motion
if True:
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

    # source frames 
    cmds.playbackOptions(min=min_time, max=max_time)
    total_frames = int(max_time - min_time + 1)
    frames = range(0, total_frames)
    print("Total number of frames:", total_frames)

# src Tpose trf 
print("src")
if True:
    src_zero_trfs = []
    src_Tpose_rots = []
    # zero_rot_data = []
    object_name = "Hips"
    joint_hierarchy = get_joint_hierarchy(object_name)
    i=0
    for object_name in joint_hierarchy:
        if object_name not in src_to_tgt_map.keys():
            continue
        src_zero_trf = get_rot_matrix(object_name)
        src_zero_trfs.append(src_zero_trf)
        src_Tpose_rot = get_rotation(object_name)
        src_Tpose_rots.append(src_Tpose_rot)
        # print("{}: {}".format(object_name, src_Tpose_rot))

        # src_angle = get_rotation(object_name)
        # print(src_angle)
# tgt zero rot trf 
print("TGT")
if True:
    tgt_zero_trfs = []
    tgt_Tpose_rots = []
    object_name = "Bip001FBXASC032Pelvis"
    joint_hierarchy = get_joint_hierarchy(object_name)
    for object_name in joint_hierarchy:
        if object_name not in src_to_tgt_map.values():
            continue
        tgt_zero_trf = get_rot_matrix(object_name) # global coordinate?
        tgt_zero_trfs.append(tgt_zero_trf)
        tgt_Tpose_rot = get_rotation(object_name)
        tgt_Tpose_rots.append(tgt_Tpose_rot)
        # print("{}: {}".format(object_name, tgt_Tpose_rot))

# src motions 
print("src motion")
if True:
    src_rots = []
    object_name = "Hips"
    joint_hierarchy = get_joint_hierarchy(object_name)
    for frame in frames:
        cmds.currentTime(frame)
        src_frame_rot = []
        for object_name in joint_hierarchy:
            if object_name not in src_to_tgt_map.keys():
                continue
            src_rot = get_rotation(object_name)
            src_frame_rot.append(src_rot)
            # if frame==0:
            #     print("{}: {}".format(object_name, src_rot))
        src_rots.append(src_frame_rot)


""" update to target """
# targetDir = "D:/2024_KAI_Retargeting/bear.fbx"
# mel.eval('FBXImport -f"{}"'.format(targetDir))
if True:
    for i, (src_joint, tgt_joint) in enumerate(src_to_tgt_map.items()):
        if i!=0:
            continue

        # update to tgt: translation of hip
        perjoint_data = datas[i] # datas
        if i==0:
            array = ["translateX", "translateY", "translateZ",]
            for eid, attr in enumerate(array): 
                value = perjoint_data[attr] 
                for (times, tran) in value: 
                    cmds.setKeyframe(tgt_joint, attribute=attr, t=times, v=tran)

        # get rotation 
        array = ['rotateX', 'rotateY', 'rotateZ']
        
        # update to tgt
        tgt_zero_trf = tgt_zero_trfs[i]
        # src zero trf 
        src_zero_trf = src_zero_trfs[i]
        inv_src_zero_trf = np.linalg.inv(src_zero_trf)
        # print("{}:{}".format(i, np.matmul(inv_src_zero_trf, tgt_zero_trf)))

        # Tpose rot 
        src_Tpose_rot = np.array(src_Tpose_rots[i])
        tgt_Tpose_rot = np.array(tgt_Tpose_rots[i])
        # print("{}:{}".format(src_Tpose_rot, tgt_Tpose_rot))

        for times in frames:
            # print(times, i)
            # if None in rots:
            #     continue
            rots = np.array(src_rots[times][i])
            
            # get delta angle in source 
            src_delta_rot = rots - src_Tpose_rot # perjoint_rots
            if times==301:
                # print("rots: ", rots)
                # print("src_Tpose_rot: ", src_Tpose_rot)
                print("src_delta_rot: ", src_delta_rot)
                

            # set tgt rot
            tgt_delta_rot = np.matmul(tgt_zero_trf, np.matmul(inv_src_zero_trf, src_delta_rot))
            tgt_rot = tgt_Tpose_rot + tgt_delta_rot
            if times==301:
                print("tgt_Tpose_rot: ", tgt_Tpose_rot)
                print("tgt_delta_rot: ", tgt_delta_rot)
                print("tgt_rot: ", tgt_rot)
                new_delta = tgt_rot
                new_delta[0] = tgt_delta_rot[1]
                new_delta[1] = -tgt_delta_rot[0]
                new_delta[2] = tgt_delta_rot[2]
                print("new_delta:", new_delta)
                new_tgt_rot = tgt_Tpose_rot + new_delta
                print("new_tgt_rot: ", new_tgt_rot)
                # print("tgt_zero_trf: ", tgt_zero_trf)
                # print("inv_src_zero_trf: ", inv_src_zero_trf)
                # print("src_zero_trf: ", src_zero_trf)
                # print(src_delta_rot - tgt_delta_rot)
            
            for eid, attr in enumerate(array):
                # print("tgt_joint: {}, attr: {}, times: {}, rot: {}".format(tgt_joint, attr, times, tgt_rot[eid]))
                cmds.setKeyframe(tgt_joint, attribute=attr, t=times, v=tgt_rot[eid])
