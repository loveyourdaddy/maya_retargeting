# refine joints, hierarchy 
import maya.cmds as cmds
import copy
import numpy as np
from functions.rotations import normalize_rotmat

# joints
# 22 = 4+2+4+4+4+4
# TODO: alter_joint_name의 키을 가지기. 정말 필요한건지 확인.
template_joints = [
     "Hips","Spine","Spine1","Spine2",
     "Neck","Head", 
     "LeftShoulder","LeftArm","LeftForeArm","LeftHand", 
     "RightShoulder","RightArm","RightForeArm","RightHand", 
     "LeftUpLeg","LeftLeg","LeftFoot","LeftToeBase",
     "RightUpLeg","RightLeg","RightFoot","RightToeBase"
    ]

alter_joint_name = {
    "Hips":["Root", "Pelvis", "LowerTorso"], 
    "Spine":["UpperTorso",], 
    "Spine1":["chest", "spine_1", "spine_01"], 
    "Spine2":["chestUpper", "spine_2", "spine_02"], 

    "Neck":["neck_01",], 
    "Head":["head",], 

    "LeftShoulder": ["LFBXASC032Clavicle", "Clavicle_l", "LeftUpperArm", "shoulder_L", "upperarm_l"],
    "LeftArm":["LFBXASC032UpperArm", "LeftLowerArm", "upperArm_L", "lowerarm_l"],
    "LeftForeArm":["LFBXASC032Forearm", "lowerArm_L", "lowerarm_in_l"],
    "LeftHand": ["LFBXASC032Hand", "hand_L", "lowerarm_out_l"],

    "RightShoulder":["RFBXASC032Clavicle", "Clavicle_r", "RightUpperArm", "shoulder_R", "upperarm_r"],
    "RightArm":["RFBXASC032UpperArm", "RightLowerArm", "upperArm_R", "lowerarm_r"], 
    "RightForeArm":["RFBXASC032Forearm", "lowerArm_R", "lowerarm_in_r"], 
    "RightHand":["RFBXASC032Hand", "hand_R", "lowerarm_out_r"], 

    "LeftUpLeg":['LFBXASC032Thigh', 'upperLeg_L', 'upperReg_L', 'LeftUpperLeg', 'thigh_l'],
    "LeftLeg":  ['LFBXASC032Calf',  'lowerLeg_L', 'lowerReg_L', 'LeftLowerLeg', 'calf_l'], 
    "LeftFoot":['LFBXASC032Foot', 'foot_L'], 
    "LeftToeBase":['LFBXASC032Toe0', 'toes_L'], 

    "RightUpLeg":['RFBXASC032Thigh', 'upperLeg_R', 'upperReg_R', 'RightUpperLeg', 'thigh_r'], 
    "RightLeg":  ['RFBXASC032Calf',  'lowerLeg_R', 'lowerReg_R', 'RightLowerLeg', 'calf_r'], 
    "RightFoot":['RFBXASC032Foot', 'foot_R'], 
    "RightToeBase":['RFBXASC032Toe0', 'toes_R'], 
    }

finger_alter_joint_name = {
    # finger 
    "LeftHandThumb1":["LeftHandThumb1", "Thumb_01_l"], 
    "LeftHandThumb2":["LeftHandThumb2", "Thumb_02_l"], 
    "LeftHandThumb3":["LeftHandThumb3", "Thumb_03_l"], 

    "LeftHandIndex1":["LeftHandIndex1", "Index_01_l"], 
    "LeftHandIndex2":["LeftHandIndex2", "Index_02_l"], 
    "LeftHandIndex3":["LeftHandIndex3", "Index_03_l"], 

    "LeftHandMiddle1":["LeftHandMiddle1", "Middle_01_l"], 
    "LeftHandMiddle2":["LeftHandMiddle2", "Middle_02_l"], 
    "LeftHandMiddle3":["LeftHandMiddle3", "Middle_03_l"], 
    
    "LeftHandRing1":["LeftHandRing1", "Ring_01_l"], 
    "LeftHandRing2":["LeftHandRing2", "Ring_02_l"], 
    "LeftHandRing3":["LeftHandRing3", "Ring_03_l"], 
    
    "LeftHandPinky1":["LeftHandPinky1", "Pinky_01_l"], 
    "LeftHandPinky2":["LeftHandPinky2", "Pinky_02_l"], 
    "LeftHandPinky3":["LeftHandPinky3", "Pinky_03_l"], 

    # right hand
    "RightHandThumb1":["RightHandThumb1", "Thumb_01_r"],
    "RightHandThumb2":["RightHandThumb2", "Thumb_02_r"],
    "RightHandThumb3":["RightHandThumb3", "Thumb_03_r"],

    "RightHandIndex1":["RightHandIndex1", "Index_01_r"],
    "RightHandIndex2":["RightHandIndex2", "Index_02_r"],
    "RightHandIndex3":["RightHandIndex3", "Index_03_r"],

    "RightHandMiddle1":["RightHandMiddle1", "Middle_01_r"],
    "RightHandMiddle2":["RightHandMiddle2", "Middle_02_r"],
    "RightHandMiddle3":["RightHandMiddle3", "Middle_03_r"],

    "RightHandRing1":["RightHandRing1", "Ring_01_r"],
    "RightHandRing2":["RightHandRing2", "Ring_02_r"],
    "RightHandRing3":["RightHandRing3", "Ring_03_r"],

    "RightHandPinky1":["RightHandPinky1", "Pinky_01_r"],
    "RightHandPinky2":["RightHandPinky2", "Pinky_02_r"],
    "RightHandPinky3":["RightHandPinky3", "Pinky_03_r"],
}

""" hierarchy """
def get_joint_hierarchy(root_joint):
    hierarchy = []

    def traverse_joint(joint):
        # import pdb; pdb.set_trace()
        children = cmds.listRelatives(joint, children=True, type='joint') or []
        hierarchy.append(joint)
        for child in children:
            traverse_joint(child)

    traverse_joint(root_joint)
    return hierarchy

def find_root_joints(all_joints):
    root_joints = []
    
    # find root joint
    for joint in all_joints:
        parents = cmds.listRelatives(joint, parent=True)
        # print("joint {}, parents {}".format(joint, parents))

        # parent가 없거나, parent가 joint가 아니면, root joint에 추가
        if not parents or (cmds.nodeType(parents[0]) != 'joint'):
            root_joints.append(joint)

    # find best root joint: 
    children_of_roots = [[] for _ in range(len(root_joints))]
    list_index = []
    for i, root_joint in enumerate(root_joints):
        hierarchy = get_joint_hierarchy(root_joint)
        hierarchy = rename_joint_by_template(hierarchy)
        children_of_roots[i] = select_joints_by_template(hierarchy)
        list_index.append(len(children_of_roots[i]))

    # TODO 여러 skeleton chain에서 best chain을 고르는 방법. -> list로 해도 될까?
    # max_index = list_index.index(max(list_index))
    # return root_joints #[max_index]
    
    max_index = list_index.index(max(list_index))
    return root_joints[max_index]

def get_parent_joint(joint):
    parent = cmds.listRelatives(joint, parent=True)
    if parent:
        return parent[0]
    else:
        return None

def get_top_level_nodes():
    return cmds.ls(assemblies=True)

""" rename """
# joint name -> template name (alter)
def rename_joint_by_template(joints): 
    ret_joints = []
    for joint in joints:
        # if joint name in namespace, remove namespace
        if ":" in joint:
            joint = joint.split(":")[-1]

        # replace joint name to template key name
        check = False
        for key_joint, alter_joints in alter_joint_name.items():
            for alter_joint in alter_joints:
                # list 안에 있고, 이미 등록되지 않다면
                if (joint.lower() in alter_joint.lower() or alter_joint.lower() in joint.lower()) and key_joint not in ret_joints:
                    joint = key_joint
                    check = True
                    # print("find")
        
        # finger 조인트: finger_포함하기
        if check==False:
            for key_joint, alter_joints in finger_alter_joint_name.items():
                for alter_joint in alter_joints:
                    # list 안에 있고, 이미 등록되지 않다면
                    if (joint.lower() in alter_joint.lower() or alter_joint.lower() in joint.lower()) and key_joint not in ret_joints:
                        joint = "finger_"+key_joint
                    
        ret_joints.append(joint)

    return ret_joints

""" refine hierarchy """
# select body skeleton (not finger) 
def select_joints_by_template(joints):
    refined_joints = []
    added_template_joints = []
    alter_joint_name_ = copy.deepcopy(alter_joint_name)
    for template_joint in template_joints:
        for joint in joints:
            alter_joint = joint
            for temp_name, alter_names in alter_joint_name_.items():
                changed = False
                for alter_name in alter_names:
                    if joint in alter_name or alter_name in joint:
                        alter_joint = temp_name
                        changed = True
                        break
                if changed:
                    # altername에서 찾았으면 제거하기
                    del alter_joint_name_[temp_name]
                    break

            # 1. joint in template joint,
            # 2. not finger
            # 3. not already exist in the list
            if (template_joint.lower() in alter_joint.lower() or alter_joint.lower() in template_joint.lower()) and \
                    "Thumb" not in joint and \
                    "Index" not in joint and \
                    "Middle" not in joint and \
                    "Ring" not in joint and \
                    "Pinky" not in joint and \
                    joint not in refined_joints and \
                    template_joint not in added_template_joints:
                # add 
                refined_joints.append(joint)
                added_template_joints.append(template_joint)

                # 체크가 되었으면 joints에서 제거하기
                joints.remove(joint)
                break
    
    return refined_joints

def get_common_hierarchy_bw_src_and_tgt(src_joints_origin, src_joints_template, tgt_joints_origin, tgt_joints_template):
    # get division
    def get_division(joint_hierarchy):
        ''' 
        division 조건
        - children이 1개 초과
        '''
        
        def check_joint_by_template_names(joint_name, template_names):
            for template_name in template_names:
                if joint_name.lower() in template_name.lower() or template_name.lower() in joint_name.lower():
                    return True
            return False
        
        # division = []
        root_names = ["Root", "hip", "Pelvis", "LowerTorso"]
        spine_names = ["spine", "chest", "UpperTorso"]

        root_joints, spine_joints = [], []
        for i, joint_name in enumerate(joint_hierarchy):
            check = False 
            children = cmds.listRelatives(joint_name, children=True, type='joint')

            # 예외처리: 조인트가 ee 
            if children is None:
                continue

            # 만약 child의 child가 없다면, children에서 제외해주기. 
            filtered_children = []
            for child in children:
                # print(child)
                if cmds.listRelatives(child, children=True, type='joint') is not None:
                    filtered_children.append(child)
            children = filtered_children

            # division0: root 
            if children is not None and len(children)>1:
                if check_joint_by_template_names(joint_name, root_names):
                    root_joints.append(joint_name)
                    check = True
            if check:
                continue

            # division1: spine 
            if children is not None and len(children)>1:
                if check_joint_by_template_names(joint_name, spine_names):
                    spine_joints.append(joint_name)
                    check = True
            if check:
                continue

        # 만약 root joint을 찾을 수 없다면, 이름으로 찾지 않고 skeletal chain으로 찾기
        if len(root_joints)==0:
            return -1, "", -1, ""

        # 가장 마지막을 division으로 설정
        root_name = root_joints[-1]
        root_jid = joint_hierarchy.index(root_name)
        spine_name = spine_joints[-1]
        spine_jid = joint_hierarchy.index(spine_name)

        return root_jid, root_name, spine_jid, spine_name

    # jid, name
    tgt_root_div_jid, tgt_root_div, tgt_spine_div_jid, tgt_spine_div = get_division(tgt_joints_origin)
    src_root_div_jid, src_root_div, src_spine_div_jid, src_spine_div = get_division(src_joints_origin)

    # 만약 root joint을 찾을 수 없다면, 분기점으로 name을 바꿔주기
    if tgt_root_div_jid==-1:
        def find_skeleton_by_hierarchy(joints_wo_name):
            # 가정: root -> spine (-> left arm -> right arm) -> left leg -> right leg 
            root_div_jid = -1
            spine_div_jid = -1
            ee_joints = []
            for jid, tgt_joint in enumerate(joints_wo_name):
                children = cmds.listRelatives(tgt_joint, children=True)
                if children is not None:
                    children = [child for child in children if children and cmds.nodeType(child) == 'joint']
                    if len(children)==0:
                        children = None
                # print("tgt joint {} children {}".format(tgt_joint, children))

                # root 
                if children is not None and len(children)>1 and root_div_jid==-1 and spine_div_jid==-1:
                    name = "tgt:Hips"
                    cmds.rename(tgt_joint, name)
                    joints_wo_name[jid] = name
                    root_div_jid = jid
                    root_div = name
                    # print("tgt root div")
                    continue

                # spine
                if children is not None and len(children)>1 and root_div_jid!=-1 and spine_div_jid==-1:
                    name = "tgt:Spine"
                    cmds.rename(tgt_joint, name)
                    joints_wo_name[jid] = name
                    spine_div_jid = jid
                    spine_div = name
                    # print("tgt spine div")
                    continue
                
                if children is None: # and len(children)==0 
                    if len(ee_joints)==0:
                        name = "tgt:LeftHand"
                        joints_wo_name[jid] = name
                    elif len(ee_joints)==1:
                        name = "tgt:RightHand"
                        joints_wo_name[jid] = name
                    elif len(ee_joints)==2:
                        name = "tgt:Head"
                        joints_wo_name[jid] = name
                    elif len(ee_joints)==3:
                        name = "tgt:LeftToeBase"
                        joints_wo_name[jid] = name
                    elif len(ee_joints)==4:
                        name = "tgt:RightToeBase"
                        joints_wo_name[jid] = name
                    else:
                        raise("ee joints are more than 5")
                    ee_joints.append(jid)
                    cmds.rename(tgt_joint, name)
            
            # 분기점 사이의 조인트의 이름을 바꿔주기
            spine_idx = 0
            for jid, tgt_joint in enumerate(joints_wo_name):
                name = None 

                # spine 
                if jid > root_div_jid and jid < spine_div_jid:
                    spine_idx += 1
                    name = "tgt:Spine" + str(spine_idx)
                    joints_wo_name[jid] = name
                # left arm
                if jid > spine_div_jid and jid < ee_joints[0]:
                    if jid == spine_div_jid+1:
                        name = "tgt:LeftShoulder"
                    elif jid == spine_div_jid+2:
                        name = "tgt:LeftArm"
                    elif jid == spine_div_jid+3:
                        name = "tgt:LeftForeArm"
                    joints_wo_name[jid] = name
                # right arm
                if jid > ee_joints[0] and jid < ee_joints[1]:
                    if jid == spine_div_jid+1:
                        name = "tgt:RightShoulder"
                    elif jid == spine_div_jid+2:
                        name  = "tgt:RightArm"
                    elif jid == spine_div_jid+3:
                        name = "tgt:RightForeArm"
                    joints_wo_name[jid] = name 
                # neck
                if jid > ee_joints[1] and jid < ee_joints[2]:
                    if jid == spine_div_jid+1:
                        name = "tgt:Neck"
                        joints_wo_name[jid] =name 
                # left leg
                if jid > ee_joints[2] and jid < ee_joints[3]:
                    if jid == ee_joints[2]+1:
                        name = "tgt:LeftUpLeg"
                    elif jid == ee_joints[2]+2:
                        name=  "tgt:LeftLeg"
                    elif jid == ee_joints[2]+3:
                        name = "tgt:LeftFoot"
                    joints_wo_name[jid] = name 
                # right leg
                if jid > ee_joints[3] and jid < ee_joints[4]:
                    if jid == ee_joints[3]+1:
                        name = "tgt:RightUpLeg"
                    elif jid == ee_joints[3]+2:
                        name = "tgt:RightLeg"
                    elif jid == ee_joints[3]+3:
                        name = "tgt:RightFoot"
                    joints_wo_name[jid] = name 
                # rename 
                if name is not None:
                    cmds.rename(tgt_joint, name)

            return joints_wo_name, root_div_jid, root_div, spine_div_jid, spine_div
        tgt_joints_template, tgt_root_div_jid, tgt_root_div, tgt_spine_div_jid, tgt_spine_div = find_skeleton_by_hierarchy(tgt_joints_origin)

    # remove namespace
    src_root_div = src_root_div.split(':')[-1]
    tgt_root_div = tgt_root_div.split(':')[-1]
    src_spine_div = src_spine_div.split(':')[-1]
    tgt_spine_div = tgt_spine_div.split(':')[-1]

    ''' get common joints 
    Divison 예외처리: 
    - 만약 joint가 spine div조인트를 넘어갔고, 리스트에 없다면 
    - 마지막 조인트를 1개 빼주고(spine이 1개 이상있다고 가정.) division joint을 넣어주기
    '''
    def get_common_substring(str1_, str2_):
        str1 = str1_.lower() 
        str2 = str2_.lower() 

        m = len(str1)
        n = len(str2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        max_length = 0
        end_position = 0
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if str1[i-1] == str2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                    if dp[i][j] > max_length:
                        max_length = dp[i][j]
                        end_position = i
                        
        return str1[end_position - max_length:end_position]
    
    def check_string_in_list(string, string_list):
        string_list_lower = [value.lower() for value in string_list]
        string_lower = string.lower()
        if string_lower in string_list_lower or any(val in string_lower for val in string_list_lower):
            return True
        else:
            return False
    
    def check_common_string_in_value_of_other_list(src_joint, tgt_joint):
        common_string = get_common_substring(src_joint, tgt_joint)

        # 본인의 키를 찾기. 
        # common string이 alter_joint_name의 values에 있는지 확인 
        check_find_key = False
        for key_common, values in alter_joint_name.items():
            values_lower = [value.lower() for value in values]
            if common_string in values_lower:
                check_find_key = True
                break
        
        # 다른 키에 속하는지 확인
        # 다른 키에 속하는 경우, 제외해주기.
        if check_find_key:
            check_other_key = False
            for key, values in alter_joint_name.items():
                # 본인 key는 서치에서 제외
                if key==key_common:
                    continue

                # 방향 제외 (_l, _r_)
                values_wo_lr = [value[:-2] for value in values]
   
                # 다른 key 확인
                # 다른 조인트의 values에 속하지 않고, finger가 아닌 경우 
                if (check_string_in_list(src_joint, values) or check_string_in_list(tgt_joint, values) or\
                    check_string_in_list(src_joint, values_wo_lr) or check_string_in_list(tgt_joint, values_wo_lr)) and\
                        "finger" not in common_string:
                    check_other_key = True
                    break
            if check_other_key:
                return True
            
        return False

    ''' get common joints 
    Divison 예외처리: 
    - 만약 joint가 spine div조인트를 넘어갔고, 리스트에 없다면 
    - 마지막 조인트를 1개 빼주고(spine이 1개 이상있다고 가정.) division joint을 넣어주기
    '''
    src_common_joint = []
    tgt_common_joint = []
    src_indices = []
    tgt_indices = []
    root_check_flag = False
    spine_check_flag = False
    for src_idx, src_joint in enumerate(src_joints_template):
        check = False
        for tgt_idx, tgt_joint in enumerate(tgt_joints_template):
            src_joint_renamed = src_joint.split(':')[-1]
            tgt_joint_renamed = tgt_joint.split(':')[-1]

            # find common joint
            if (src_joint_renamed.lower() in tgt_joint_renamed.lower() or tgt_joint_renamed.lower() in src_joint_renamed.lower()) \
                    and src_joint not in src_common_joint and tgt_joint not in tgt_common_joint: 
                # print("src {} {} tgt {} {}".format(src_idx, src_joint, tgt_idx, tgt_joint))
                # 다른 조인트에 속하는 경우, 제외해주기
                if check_common_string_in_value_of_other_list(src_joint, tgt_joint):
                    continue

                # add root division
                if root_check_flag==False and src_idx > src_root_div_jid and tgt_idx > tgt_root_div_jid:
                    if src_joint not in src_common_joint:
                        if len(src_common_joint)==0:
                            src_common_joint.append(src_root_div)
                            src_indices.append(src_root_div_jid)
                        else:
                            src_common_joint[-1] = src_root_div
                            src_indices[-1] = src_root_div_jid
                        print("add src root div")

                    if tgt_joint not in tgt_common_joint:
                        if len(tgt_common_joint)==0:
                            tgt_common_joint.append(tgt_root_div)
                            tgt_indices.append(tgt_root_div_jid)
                        else:
                            tgt_common_joint[-1] = tgt_root_div
                            tgt_indices[-1] = tgt_root_div_jid
                        print("add tgt root div")
                    root_check_flag = True

                # add spine division
                if spine_check_flag==False and src_idx > src_spine_div_jid and tgt_idx > tgt_spine_div_jid:
                    if src_joint not in src_common_joint:
                        src_common_joint[-1] = src_spine_div
                        src_indices[-1] = src_spine_div_jid
                        print("add src spine div")
                    if tgt_joint not in tgt_common_joint:
                        tgt_common_joint[-1] = tgt_spine_div
                        tgt_indices[-1] = tgt_spine_div_jid
                        print("add tgt spine div")
                    spine_check_flag = True

                # print("src {} {} tgt {} {}".format(src_idx, src_joint, tgt_idx, tgt_joint))
                src_common_joint.append(src_joint)
                tgt_common_joint.append(tgt_joint)
                src_indices.append(src_idx)
                tgt_indices.append(tgt_idx)
                check = True
                break
        if check:
            continue


    ''' Updated joint hierarchy by selected ones '''
    src_select_hierarchy, tgt_select_hierarchy = [], []
    src_name2index = {}
    tgt_name2index = {}
    for i in range(len(src_indices)):
        src_name = src_joints_origin[src_indices[i]]
        tgt_name = tgt_joints_origin[tgt_indices[i]]

        src_select_hierarchy.append(src_name)
        tgt_select_hierarchy.append(tgt_joints_template[tgt_indices[i]])

        src_name2index[src_name] = i
        tgt_name2index[tgt_name] = i
    src_joints_template = src_select_hierarchy
    tgt_joints_template = tgt_select_hierarchy

    # origin name
    tgt_select_hierarchy_origin = []
    for i in range(len(src_indices)):
        tgt_select_hierarchy_origin.append(tgt_joints_origin[tgt_indices[i]])
    tgt_joints_origin = tgt_select_hierarchy_origin

    """ ee joints """
    ee_joints = []
    for i, joint in enumerate(tgt_joints_origin):
        children = cmds.listRelatives(joint, children=True, type='joint')
        if children is None:
            ee_joints.append(joint)

    """ parent index """
    # TODO: remove. 동일함.
    # select joint hierarchy: 적은것 기준
    if len(src_indices) <= len(tgt_indices):
        joint_indices = src_indices
        joint_hierarchy = src_joints_origin
        name2index = src_name2index
        # print("src standard")
    else:
        joint_indices = tgt_indices
        joint_hierarchy = tgt_joints_origin
        name2index = tgt_name2index
        # print("tgt standard")
    
    parent_indices = []
    division = []
    child_of_divisions = []
    for i in range(len(joint_indices)):
        joint_name = joint_hierarchy[i]

        # child of joint
        children = cmds.listRelatives(joint_name, children=True, type='joint')
        if children is not None:
            children_index = []
            for child in children:
                if child not in name2index:
                    continue
                children_index.append(name2index[child])

        # get parent index
        if len(parent_indices)==0:
            # root 
            parent_j = -1
        else:
            # parent가 division이라면, division을 parent index로 
            check = False 
            for division_idx, child_of_division in enumerate(child_of_divisions):
                if i in child_of_division:
                    parent_j = division[division_idx]
                    check = True
                    break

            # 해당 없다면
            if check==False:
                parent_j = i-1
        parent_indices.append(parent_j)
        # print("joint {} {} parent {} {}".format(i, joint_name, parent_j, joint_hierarchy[parent_j]))

        # division
        # children이 있고, end effector가 아닌 경우
        if children is not None and len(children)>1 and joint_hierarchy[i] not in ee_joints:
            division_j = copy.deepcopy(i)
            division.append(division_j)
            child_of_divisions.append(children_index)
    
    return src_joints_template, tgt_joints_template, parent_indices, src_indices, tgt_indices

""" namespace """
def add_namespace(joint, namespace):
    old_name = joint

    # 만약 이미 namespace가 있다면, 제거해주기.
    if joint.find(":") != -1:
        joint = joint.split(":")[-1]

    new_name = f"{namespace}:{joint}"
    
    # print("{} -> {}".format(old_name, new_name))
    return cmds.rename(old_name, new_name)

def remove_namespace(joint):
    if joint.find(":") != -1:
        short_name = joint.split(':')[-1]
        new_name = f"{short_name}"
        return cmds.rename(joint, new_name) 
    else:
        return joint
    
def add_namespace_for_joints(joints, namespace):
    if not cmds.namespace(exists=namespace):
        cmds.namespace(add=namespace)
    
    new_joints = []
    for joint in joints:
        new_joints.append(add_namespace(joint, namespace))
    return new_joints

def add_namespace_for_meshes(meshes, namespace):
    if not cmds.namespace(exists=namespace):
        cmds.namespace(add=namespace)
    
    new_meshes = []
    for mesh in meshes:
        new_meshes.append(add_namespace(mesh, namespace))
    return new_meshes

def remove_namespace_for_joints(joints):
    new_joints = []
    for joint in joints:
        # if joint exist
        if cmds.objExists(joint):
            new_joints.append(remove_namespace(joint))
        else:
            new_joints.append(joint)
    return new_joints

""" Get prerot """
def get_prerotations(tgt_joints, tgt_locator=None, tgt_locator_rot=None):
    # (locator, joint들의) local rotation을 저장 후 나중에 복원.

    # set zero 
    if tgt_locator is not None:
        cmds.xform(tgt_locator, ro=(0,0,0), q=False, ws=False)

    # get prerot
    angle_origins = []
    prerotations = []
    for j, joint in enumerate(tgt_joints):
        # print("{} joint {}".format(j, joint))
        # zero rotation을 만들어야하는게 아닐까?
        angle_origin = cmds.xform(joint, q=True, ws=False, ro=True)
        angle_origins.append(angle_origin)

        # set zero rot and get world rot 
        cmds.xform(joint, ro=(0,0,0), q=False, ws=False)
        prerot = np.transpose(np.array(cmds.xform(joint, q=True, ws=True, matrix=True)).reshape(4,4))[:3,:3]
        prerot = normalize_rotmat(prerot)
        prerotations.append(prerot)
        # print(f"joint {j} {joint} angle {angle_origin} prerot \n{prerot}")

    # 기존 값으로 돌려주기
    if tgt_locator is not None:
        cmds.xform(tgt_locator, ro=(tgt_locator_rot), q=False, ws=False)
    for j, joint in enumerate(tgt_joints):
        angle_origin = angle_origins[j]
        cmds.xform(joint, ro=tuple(angle_origin), q=False, ws=False)
    
    return prerotations
