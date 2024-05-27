import maya.cmds as cmds
import maya.mel as mel
import math 
import numpy as np

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
            # print(object_name, "not found")
            continue
        if object_name=="Hips":
            array = ['rotateX', 'rotateY', 'rotateZ', 'translateX', 'translateY', 'translateZ']
            # print(object_name, array)
        else:
            array = ['rotateX', 'rotateY', 'rotateZ']
            # print(object_name, array)
        
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
                
                # if object_name=="Hips":
                #     print("attr:{}, value:{}".format(attr, values))
                #     print(perjoint_data[attr])
        datas.append(perjoint_data)

total_frames = max_time - min_time + 1
print("Total number of frames:", total_frames)
# print(datas[0])

""" update to target """
# targetDir = "D:/2024_KAI_Retargeting/bear.fbx"
# mel.eval('FBXImport -f"{}"'.format(targetDir))
rot_mat = np.array([[1,0,0],[0,1,0],[0,0,1]])
# rot_mat = np.array([[0,1,0],[-1,0,0],[0,0,1]])
# rot_mat = np.array([[1,0,0],[0,0,1],[0,-1,0]])
for i, (src_joint, tgt_joint) in enumerate(src_to_tgt_map.items()):
    if i!=0:
        continue

    perjoint_rots = np.array([[None, None, None]])
    perjoint_rots = np.repeat(perjoint_rots, total_frames, axis=0)

    # update to tgt 
    if True:
        perjoint_data = datas[i]
        # print("src:{}, tgt:{}, ".format(src_joint, tgt_joint))
        if src_joint=="Hips":
            array = ['rotateX', 'rotateY', 'rotateZ', "translateX", "translateY", "translateZ",]
        else:
            array = ['rotateX', 'rotateY', 'rotateZ']

        # set translation of hip
        for eid, attr in enumerate(array): 
            value = perjoint_data[attr] 
            print("attr:{}, value:{}".format(attr, value))
            
            # root trans
            if attr in ["translateX", "translateY", "translateZ"]:
                for (times, tran) in value: # trans
                    cmds.setKeyframe(tgt_joint, attribute=attr, t=times, v=tran)
            # rotations
            else:
                for (times, rot) in value:
                    perjoint_rots[int(times), eid] = rot
    
        array = ['rotateX', 'rotateY', 'rotateZ']
        for times, rots in enumerate(perjoint_rots):
            src_rot = np.array(rots)
            if None in rots:
                continue
                
            # rotated_rots = np.matmul(rot_mat, rots) 
            # if int(times) == 0:
            #     print(rots)
            #     print(rotated_rots)
            
            for eid, attr in enumerate(array):
                if int(times) == 0:
                    print(rots[eid])
                    # print(rotated_rots[eid])
                # rot = rotated_rots[eid]
                tgt_rot = src_rot[eid]
                # print("tgt_joint: {}, attr: {}, times: {}, rot: {}".format(tgt_joint, attr, times, rot))
                cmds.setKeyframe(tgt_joint, attribute=attr, t=times, v=tgt_rot)
