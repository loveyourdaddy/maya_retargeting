import maya.cmds as cmds
import maya.mel as mel
import math 
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

def get_transform_rotation(node_name):
    if cmds.objExists(node_name): #  and cmds.objectType(node_name) == 'transform'
        rotateX = cmds.getAttr(f"{node_name}.rotateX")
        rotateY = cmds.getAttr(f"{node_name}.rotateY")
        rotateZ = cmds.getAttr(f"{node_name}.rotateZ")
        return rotateX, rotateY, rotateZ
    else:
        return None

# def 
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

# object_name = "Hips"
# joint_hierarchy = get_joint_hierarchy(object_name)

""" src motion """
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

total_frames = max_time - min_time + 1
# print("Total number of frames:", total_frames)


""" calculate perjoint delta of src """
deltas = []
array = ['rotateX', 'rotateY', 'rotateZ']
for i, perjoint_data in enumerate(datas):
    # if i!=0:
    #     continue
    perjoint_value = {'rotateX': [], 'rotateY': [], 'rotateZ': []}

    # tuple to list 
    perjoint_times = []
    perjoint_delta = [] 
    for attr in array: 
        perattr_times = []
        perattr_delta = []
        for perframe_data in perjoint_data[attr]:
            perattr_times.append(perframe_data[0])
            perattr_delta.append(perframe_data[1])
        perjoint_times.append(perattr_times)
        perjoint_delta.append(perattr_delta)

    for aid, attr in enumerate(array):
        perattr_data = perjoint_delta[aid]
        Tpose_rot = copy.deepcopy(perattr_data[0])
        # print("Tpose_rot: ", Tpose_rot)
        for f, perframe_data in enumerate(perattr_data):
            perjoint_delta[aid][f] = perframe_data - Tpose_rot
        perjoint_value[attr] = list(zip(perjoint_times[aid], perjoint_delta[aid]))
    
    deltas.append(perjoint_value)


""" get Tpose value of tgt """
array = ['rotateX', 'rotateY', 'rotateZ']
tgt_Tpose = []
object_name = "Bip001FBXASC032Pelvis"
joint_hierarchy = get_joint_hierarchy(object_name)
for object_name in joint_hierarchy:
    if object_name not in src_to_tgt_map.values():
        continue
    rotation = get_transform_rotation(object_name)
    tgt_Tpose.append(rotation)


""" update to target """
# targetDir = "D:/2024_KAI_Retargeting/bear.fbx"
# mel.eval('FBXImport -f"{}"'.format(targetDir))
# exception = [7,8,9,10, 15,16,17,18] 
if True:
    for i, (src_joint, tgt_joint) in enumerate(src_to_tgt_map.items()):
        print("i {}, src_joint {}, tgt_joint {}".format(i, src_joint, tgt_joint))
        # if i!=0:
        #     continue

        # update to tgt: translation of hip
        if i==0:
            perjoint_data = datas[i] # datas
            array = ["translateX", "translateY", "translateZ",]
            for eid, attr in enumerate(array): 
                value = perjoint_data[attr] 
                for (times, tran) in value: 
                    cmds.setKeyframe(tgt_joint, attribute=attr, t=times, v=tran)

        # get rotation 
        perjoint_data = deltas[i]
        array = ['rotateX', 'rotateY', 'rotateZ']
        perjoint_rots = np.array([[None, None, None]])
        perjoint_rots = np.repeat(perjoint_rots, total_frames, axis=0)
        for eid, attr in enumerate(array): 
            value = perjoint_data[attr]
            for (times, rot) in value:
                perjoint_rots[int(times), eid] = rot

        # update to tgt
        array = ['rotateX', 'rotateY', 'rotateZ']
        # print("tgt_Tpose:", tgt_Tpose)
        tgt_joint_Tpose = tgt_Tpose[i]
        # print("tgt_joint_Tpose:", tgt_joint_Tpose)
        for times, rots in enumerate(perjoint_rots):
            src_rot = np.array(rots)
            if None in rots:
                continue
            # print("src_rot:", src_rot)
            
            for eid, attr in enumerate(array):
                if src_rot[eid] is None:
                    continue
                
                if eid==0:
                    tgt_rot = tgt_joint_Tpose[0] + src_rot[1]
                elif eid==1:
                    if i not in exception: # normal
                        tgt_rot = tgt_joint_Tpose[1] + -src_rot[0]
                    else:
                        tgt_rot = tgt_joint_Tpose[1] + src_rot[0]
                else:
                    tgt_rot = tgt_joint_Tpose[2] - src_rot[2]
                    # if i not in exception: # normal
                    #     tgt_rot = tgt_joint_Tpose[2] + src_rot[2]
                    # else: 
                    #     tgt_rot = tgt_joint_Tpose[2] - src_rot[2]

                # print("tgt_joint: {}, attr: {}, times: {}, rot: {}".format(tgt_joint, attr, times, rot))
                cmds.setKeyframe(tgt_joint, attribute=attr, t=times, v=tgt_rot)
