import maya.cmds as cmds
from functions.joints import *
from functions.keyframe import *
from functions.rotations import *
from functions.motion import *

''' common joint hierarchy '''
def get_common_src_tgt_joint_hierarchy(src_joints_origin, src_joints_template, tgt_joints_origin, tgt_joints_template):
    # refine joint hierarchy
    parent_indices, src_indices, tgt_indices,\
        = get_common_hierarchy_bw_src_and_tgt(src_joints_origin, src_joints_template, tgt_joints_origin, tgt_joints_template)

    # templated: refined joint에서 인덱스을 얻을 후, tgt joints에서 뽑기
    src_joints_common = [src_joints_origin[i] for i in src_indices]
    tgt_joints_common = [tgt_joints_origin[i] for i in tgt_indices]

    return src_joints_common, tgt_joints_common, src_indices, tgt_indices, parent_indices

def get_common_hierarchy_bw_src_and_tgt(src_joints_origin, src_joints_template, tgt_joints_origin, tgt_joints_template):
    # jid, name
    tgt_root_div_jid, tgt_root_div, tgt_spine_div_jid, tgt_spine_div = get_division_by_name(tgt_joints_origin, tgt_joints_template)
    src_root_div_jid, src_root_div, src_spine_div_jid, src_spine_div = get_division_by_name(src_joints_origin, src_joints_template)

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

    # get common joints 
    ''' 
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
        # Hips 이름 중복에 대한 예외처리
        # 이름이 같고, src_root_div_jid보다 작다면, continue
        if src_joint.lower() == src_root_div.lower() and src_idx < src_root_div_jid:
            continue

        check = False
        for tgt_idx, tgt_joint in enumerate(tgt_joints_template):
            src_joint_renamed = src_joint.split(':')[-1]
            tgt_joint_renamed = tgt_joint.split(':')[-1]

            # find common joint
            if (src_joint_renamed.lower() in tgt_joint_renamed.lower() or tgt_joint_renamed.lower() in src_joint_renamed.lower()) \
                    and (src_joint not in src_common_joint and tgt_joint not in tgt_common_joint): # root_check_flag==False or spine_check_flag==False)

                # 다른 조인트에 속하는 경우, 제외해주기
                if check_common_string_in_value_of_other_list(src_joint, tgt_joint):
                    continue

                # add root division forcely: division 조인트를 넣어주기
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
                    break

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
                    break

                print("src {} {} tgt {} {}".format(src_idx, src_joint, tgt_idx, tgt_joint))
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

    # origin name
    tgt_select_hierarchy_origin = []
    for i in range(len(src_indices)):
        tgt_select_hierarchy_origin.append(tgt_joints_origin[tgt_indices[i]])

    """ ee joints """
    ee_joints = []
    for i, joint in enumerate(tgt_select_hierarchy_origin):
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
        joint_hierarchy = tgt_select_hierarchy_origin
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
    
    return parent_indices, src_indices, tgt_indices

def check_joint_by_template_names(joint_name, template_names):
    for template_name in template_names:
        if joint_name.lower() in template_name.lower() or template_name.lower() in joint_name.lower():
            return True
    return False

def get_division_by_name(joint_hierarchy_origin, joint_hierarchy_template):
    ''' 
    division 조건
    - children이 1개 초과
    '''
    # division
    root_names = alter_joint_name["Hips"] + ["Hips"]
    spine_names = alter_joint_name["Spine"] + ["spine", "chest"]

    root_joints, spine_joints = [], []
    for i, joint_name in enumerate(joint_hierarchy_origin):
        children = cmds.listRelatives(joint_name, children=True, type='joint')

        # 예외처리: 조인트가 ee 
        if children is None:
            continue

        # 만약 child의 child가 없다면, children에서 제외해주기. 
        filtered_children = []
        for child in children:
            if cmds.listRelatives(child, children=True, type='joint') is not None:
                filtered_children.append(child)
        children = filtered_children

        if joint_name in joint_hierarchy_origin:
            jid = joint_hierarchy_origin.index(joint_name)
            joint_name_template = joint_hierarchy_template[jid]
        # print("joint {} joint_name_template {}".format(joint_name, joint_name_template))

        # division0: root 
        if children is not None and len(children)>1 and check_joint_by_template_names(joint_name_template, root_names):
            root_joints.append(joint_name_template)
            continue

        # division1: spine 
        if children is not None and len(children)>1 and check_joint_by_template_names(joint_name_template, spine_names):
            spine_joints.append(joint_name_template)
            continue

    # 만약 root joint을 찾을 수 없다면, 이름으로 찾지 않고 skeletal chain으로 찾기
    if len(root_joints)==0:
        return -1, "", -1, ""

    # 가장 마지막을 division으로 설정
    # Spine 
    spine_name = spine_joints[-1]
    spine_jid = joint_hierarchy_template.index(spine_name)

    # Root: 마지막 root 및 spine joint 보다 인덱스가 작은것 
    root_joints = [joint for joint in root_joints if joint_hierarchy_template.index(joint) < spine_jid]
    root_name = root_joints[-1]
    root_jid = len(joint_hierarchy_template) - 1 - joint_hierarchy_template[::-1].index(root_name) # 리스트를 뒤집고 첫 번째 'Hips'의 인덱스를 찾은 후, 원래 리스트로 뒤집기

    return root_jid, root_name, spine_jid, spine_name

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
            # 1 다른 조인트의 values에 속하지 않고, 2 finger가 아닌 경우, 3 hand가 아닌 경우 (hand_L, hand_R이 겹칠수있음)
            if (check_string_in_list(src_joint, values) or check_string_in_list(tgt_joint, values) or\
                check_string_in_list(src_joint, values_wo_lr) or check_string_in_list(tgt_joint, values_wo_lr)) and\
                    "finger" not in common_string and \
                    key != "RightHand" and key != "LeftHand":
                check_other_key = True
                break
        if check_other_key:
            return True
        
    return False
