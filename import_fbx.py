import maya.cmds as cmds
import maya.mel as mel

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

src_to_tgt_map = {}
src_to_tgt_map["Hips"] = "Bip001FBXASC032Pelvis"
src_to_tgt_map["Spine"] = "Bip001FBXASC032Spine"
src_to_tgt_map["Spine1"] ="Bip001FBXASC032Spine1"
src_to_tgt_map["Spine2"] ="Bip001FBXASC032Spine2"
src_to_tgt_map["Neck"] = "Bip001FBXASC032Neck"
src_to_tgt_map["Neck1"] = "Bip001FBXASC032Head"
src_to_tgt_map["head"] = "Bip001FBXASC032HeadNub"
src_to_tgt_map["LeftShoulder"] = "Bip001FBXASC032LFBXASC032Clavicle"
src_to_tgt_map["LeftArm"] = "Bip001FBXASC032LFBXASC032UpperArm"
src_to_tgt_map["LeftForeArm"] = "Bip001FBXASC032LFBXASC032Forearm"
src_to_tgt_map["LeftHand"] = "Bip001FBXASC032LFBXASC032Hand"
src_to_tgt_map["RightShoulder"] = "Bip001FBXASC032RFBXASC032Clavicle"
src_to_tgt_map["RightArm"] = "Bip001FBXASC032RFBXASC032UpperArm"
src_to_tgt_map["RightForeArm"] = "Bip001FBXASC032RFBXASC032Forearm"
src_to_tgt_map["RightHand"] = "Bip001FBXASC032RFBXASC032Hand"
src_to_tgt_map["RightUpLeg"] = "Bip001FBXASC032LFBXASC032Thigh"
src_to_tgt_map["RightLeg"] = "Bip001FBXASC032LFBXASC032Calf"
src_to_tgt_map["RightFoot"] = "Bip001FBXASC032LFBXASC032Foot"
src_to_tgt_map["RightToeBase"] = "Bip001FBXASC032LFBXASC032Toe0"
src_to_tgt_map["LeftUpLeg"] = "Bip001FBXASC032RFBXASC032Thigh"
src_to_tgt_map["LeftLeg"] = "Bip001FBXASC032RFBXASC032Calf"
src_to_tgt_map["LeftFoot"] = "Bip001FBXASC032RFBXASC032Foot"
src_to_tgt_map["LeftToeBase"] = "Bip001FBXASC032RFBXASC032Toe0"


# strDir = "D:/2024_KAI_Retargeting/Adori/animation/0055_Freestyle002_03_RT0214.fbx"
# mel.eval('FBXImport -f"{}"'.format(strDir))

""" get perjoint_data """
# get hierarchy 
object_name = "Hips"
joint_hierarchy = get_joint_hierarchy(object_name)

# Get perjoint_data
datas = []
perjoint_data = {'rotateX': [], 'rotateY': [], 'rotateZ': [], 
                 'translateX': [], 'translateY': [], 'translateZ': []}
max_val = 0
# min_val = 0
# 이게 모든 조인트에 대해서 가지고 있는건가?
for object_name in joint_hierarchy:
    if object_name not in src_to_tgt_map.keys():
        continue
    if object_name=="Hips":
        array = ['rotateX', 'rotateY', 'rotateZ', 'translateX', 'translateY', 'translateZ']
    else:
        array = ['rotateX', 'rotateY', 'rotateZ']
    
    print(object_name)
    for attr in array:
        if cmds.keyframe(f'{object_name}.{attr}', query=True, keyframeCount=True) > 0:
            times = cmds.keyframe(f'{object_name}.{attr}', query=True, timeChange=True)
            values = cmds.keyframe(f'{object_name}.{attr}', query=True, valueChange=True)
            max_time = max(times)
            if max_time>max_val:
                max_val = max_time
            perjoint_data[attr] = list(zip(times, values))
    datas.append(perjoint_data)
# print(len(datas[0]["translateX"]))
# print(len(datas))

""" update """
duration = 0.25
if False:
    len_frame = int(max_val / duration) + 1
    print("len_frame:", len_frame) # 2569.0 # 642.25

    rot_x = [None] * len_frame
    rot_y = [None] * len_frame
    rot_z = [None] * len_frame
    trs_x = [None] * len_frame
    trs_y = [None] * len_frame
    trs_z = [None] * len_frame
    # print(len(rot_x)) # 642.25 time = 2,569번째 frame
    for jid, perjoint_data in datas:
        for attr, perjoint_data in perjoint_data.items():
            if attr == "rotateX":
                rot_array = rot_x
            elif attr == "rotateY": 
                rot_array = rot_y
            elif attr == "rotateZ":
                rot_array = rot_z
            elif attr == "translateX":
                rot_array = trs_x
            elif attr == "translateY": 
                rot_array = trs_y
            elif attr == "translateZ":
                rot_array = trs_z
            else:
                raise ValueError("")

            for i, values in enumerate(perjoint_data):
                time = values[0]
                frame = int(time/duration)

                rot = values[1]
                rot_array[frame] = rot 
                # print("i {}: perjoint_data{}".format(i, rot))
    # print(rot_x)

# # # load target 
# # targetDir = "D:/2024_KAI_Retargeting/bear.fbx"
# # # mel.eval('FBXImport -f"{}"'.format(targetDir))
for i, (src_joint, tgt_joint) in enumerate(src_to_tgt_map.items()):
    perjoint_data = datas[i]
    print("src:{}, tgt:{}, ".format(src_joint, tgt_joint))
    if src_joint=="Hips":
        array = ['rotateX', 'rotateY', 'rotateZ', "translateX", "translateY", "translateZ",]
    else:
        array = ['rotateX', 'rotateY', 'rotateZ']

    # for attr in array: # , 'translateX', 'translateY', 'translateZ'
    #     if attr == "rotateX":
    #         perjoint_data = rot_x
    #     elif attr == "rotateY":
    #         perjoint_data = rot_y
    #     elif attr == "rotateZ":
    #         perjoint_data = rot_z
    #     elif attr == "translateX":
    #         perjoint_data = trs_x
    #     elif attr == "translateY": 
    #         perjoint_data = trs_y
    #     elif attr == "translateZ":
    #         perjoint_data = trs_z
    #     else:
    #         raise ValueError("")

    # print("perjoint_data:", perjoint_data) # perjoint_data 
    for element in array: # perjoint_data
        print("element:", element) # element 
        value = perjoint_data[element]
        # print("value:", value) # element 
        for frame, rot in value:
            if rot is not None:
                time = frame * duration
                # print("time: {}, rot: {}".format(time, rot))
                cmds.setKeyframe(tgt_joint, attribute=attr, t=time, v=rot)
