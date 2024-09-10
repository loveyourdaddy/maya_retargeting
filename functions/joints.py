# refine joints, hierarchy 
import maya.cmds as cmds
import copy

""" hierarchy """
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
    
    # find root joint 
    for joint in all_joints:
        parents = cmds.listRelatives(joint, parent=True)
        if not parents or cmds.nodeType(parents[0]) != 'joint': 
            root_joints.append(joint)

    # find best root joint
    children_of_roots = [[] for _ in range(len(root_joints))]
    list_index = []
    # import pdb; pdb.set_trace()
    for i, root_joint in enumerate(root_joints):
        hierarchy = get_joint_hierarchy(root_joint)
        hierarchy = rename_joint_by_template(hierarchy)
        # import pdb; pdb.set_trace()
        children_of_roots[i] = select_joints(hierarchy, template_joints)
        list_index.append(len(children_of_roots[i]))
        
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
    # print("alter_joint_name", alter_joint_name)
    for joint in joints:
        # if joint name in namespace, remove namespace
        if ":" in joint:
            joint = joint.split(":")[-1]

        # replace joint name to template key name 
        # print("joint", joint)
        for temp_joint, alter_joints in alter_joint_name.items():
            for alter_joint in alter_joints:
                if (joint in alter_joint or alter_joint in joint) and temp_joint not in ret_joints:
                    joint = temp_joint
                    # print("temp_joint", temp_joint)
                    
        ret_joints.append(joint)

    return ret_joints

""" refine hierarchy """
# select by template
def select_joints(joints, template_joints):
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
                # print("{} joint and {} template mapped".format(joint, template_joint))
                # template_joints.remove(template_joint)
                break
    
    return refined_joints

# select by template
# def select_joints_with_condition(joints, template_joints, condition_joints):
    # get division
    # def get_spine_division(joint_hierarchy):
    #     # import pdb; pdb.set_trace()
    #     division = []
    #     for i, joint_name in enumerate(joint_hierarchy):
    #         children = cmds.listRelatives(joint_name, children=True, type='joint')
    #         if children is None:
    #             continue
    #         # 예외처리: 만약 child의 child가 없다면, 제외해주기. 
    #         for child in children:
    #             if cmds.listRelatives(child, children=True, type='joint') is None:
    #                 children.remove(child)
    #         if children is not None and len(children)>1: # and src_joint_hierarchy[i]
    #             division.append(joint_name)
    #             if len(division)==2:
    #                 return i, joint_name
    #     raise ValueError("division not found")
    
    # tgt_spine_div_jid, tgt_spine_div = get_spine_division(joints)
    # src_spine_div_jid, src_spine_div = get_spine_division(condition_joints)
    # src_spine_div = src_spine_div.split(':')[-1]
    # tgt_spine_div = tgt_spine_div.split(':')[-1]
    # import pdb; pdb.set_trace()

    # refined_joints = []
    # added_template_joints = []
    # alter_joint_name_ = copy.deepcopy(alter_joint_name)
    # # import pdb; pdb.set_trace()
    # for template_joint in template_joints:
    #     for joint in joints:
    #         alter_joint = joint
    #         for temp_name, alter_names in alter_joint_name_.items():
    #             changed = False
    #             for alter_name in alter_names:
    #                 if joint in alter_name or alter_name in joint:
    #                     alter_joint = temp_name
    #                     changed = True
    #                     break
    #             if changed:
    #                 # altername에서 찾았으면 제거하기
    #                 del alter_joint_name_[temp_name]
    #                 break

    #         # 1. joint in template joint,
    #         # 2. not finger
    #         # 3. not already exist in the list
    #         if (template_joint.lower() in alter_joint.lower() or alter_joint.lower() in template_joint.lower()) and \
    #                 "Thumb" not in joint and \
    #                 "Index" not in joint and \
    #                 "Middle" not in joint and \
    #                 "Ring" not in joint and \
    #                 "Pinky" not in joint and \
    #                 joint not in refined_joints and \
    #                 template_joint not in added_template_joints:
    #             refined_joints.append(joint)
    #             added_template_joints.append(template_joint)

    #             # 체크가 되었으면 joints에서 제거하기
    #             joints.remove(joint)
    #             # template_joints.remove(template_joint)
    #             print("{} joint and {} template mapped".format(joint, template_joint))
    #             break
    
    # return refined_joints

def get_common_hierarchy_bw_src_and_tgt(src_joint_hierarchy, tgt_joint_hierarchy, tgt_joint_hierarchy_origin): # tgt_joints_renamed, tgt_joints
    # origin: 이름이 원래 것
    
    # get division 
    def get_spine_division(joint_hierarchy):
        # import pdb; pdb.set_trace()
        division = []
        for i, joint_name in enumerate(joint_hierarchy):
            children = cmds.listRelatives(joint_name, children=True, type='joint')
            if children is None:
                continue
            # 예외처리: 만약 child의 child가 없다면, 제외해주기. 
            for child in children:
                if cmds.listRelatives(child, children=True, type='joint') is None:
                    children.remove(child)
            if children is not None and len(children)>1 and src_joint_hierarchy[i]:
                division.append(joint_name)
                if len(division)==2:
                    return i, joint_name
        raise ValueError("division not found")
    
    tgt_spine_div_jid, tgt_spine_div = get_spine_division(tgt_joint_hierarchy_origin)
    src_spine_div_jid, src_spine_div = get_spine_division(src_joint_hierarchy)
    src_spine_div = src_spine_div.split(':')[-1]
    tgt_spine_div = tgt_spine_div.split(':')[-1]
    print("src spine div", src_spine_div)
    print("tgt spine div", tgt_spine_div)

    # get common joints 
    src_common_joint = []
    tgt_common_joint = []
    src_indices = []
    tgt_indices = []
    spine_check_flag = False
    for src_idx, src_joint in enumerate(src_joint_hierarchy):
        check = False
        for tgt_idx, tgt_joint in enumerate(tgt_joint_hierarchy):
            src_joint_renamed = src_joint.split(':')[-1]
            tgt_joint_renamed = tgt_joint.split(':')[-1]

            # find common joint
            # 1. 이름 겹치는 부분이 있음
            # 2. 이미 list에 포함되어있지 않음
            if (src_joint_renamed.lower() in tgt_joint_renamed.lower() or tgt_joint_renamed.lower() in src_joint_renamed.lower()) \
                    and src_joint not in src_common_joint and tgt_joint not in tgt_common_joint: 
                # print("src {} tgt {}".format(src_joint, tgt_joint))

                # add spine division
                # - 만약 joint가 spine div조인트를 넘어갔고, 리스트에 없다면 
                # - 마지막 조인트를 1개 빼주고(spine이 1개 이상있다고 가정.) division joint을 넣어주기
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

                src_common_joint.append(src_joint)
                tgt_common_joint.append(tgt_joint)
                src_indices.append(src_idx)
                tgt_indices.append(tgt_idx)
                check = True
                break
        if check:
            continue

    # Updated joint hierarchy by selected ones 
    src_select_hierarchy, tgt_select_hierarchy = [], []
    src_name2index = {}
    tgt_name2index = {}
    for i in range(len(src_indices)):
        src_name = src_joint_hierarchy[src_indices[i]]
        tgt_name = tgt_joint_hierarchy_origin[tgt_indices[i]]

        src_select_hierarchy.append(src_name)
        tgt_select_hierarchy.append(tgt_joint_hierarchy[tgt_indices[i]])

        src_name2index[src_name] = i
        tgt_name2index[tgt_name] = i
    src_joint_hierarchy = src_select_hierarchy
    tgt_joint_hierarchy = tgt_select_hierarchy

    # origin name
    tgt_select_hierarchy_origin = []
    for i in range(len(src_indices)):
        tgt_select_hierarchy_origin.append(tgt_joint_hierarchy_origin[tgt_indices[i]])
    tgt_joint_hierarchy_origin = tgt_select_hierarchy_origin


    """ parent index """
    # TODO: remove. 동일함.
    # select joint hierarchy: 적은것 기준
    if len(src_indices) <= len(tgt_indices):
        joint_indices = src_indices
        joint_hierarchy = src_joint_hierarchy
        name2index = src_name2index
        # print("src standard")
    else:
        joint_indices = tgt_indices
        joint_hierarchy = tgt_joint_hierarchy_origin
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

        # division
        # children이 있고, end effector가 아닌 경우
        if children is not None and len(children)>1 and joint_hierarchy[i] not in ee_joints:
            division_j = copy.deepcopy(i)
            division.append(division_j)
            child_of_divisions.append(children_index)
    
    return src_joint_hierarchy, tgt_joint_hierarchy, parent_indices, src_indices, tgt_indices

""" namespace """
def add_namespace(joint, namespace):
    new_name = f"{namespace}:{joint}"
    # print("{} -> {}".format(joint, new_name))
    return cmds.rename(joint, new_name)

def remove_namespace(joint):
    short_name = joint.split(':')[-1]
    new_name = f"{short_name}"
    return cmds.rename(joint, new_name) 

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
    return new_joints
# 이미 head가 있기 때문에 neck|head로 나오는건가?

# joints
# 22 = 4+2+4+4+4+4
template_joints = [
     "Hips","Spine","Spine1","Spine2",
     "Neck","Head", 
     "LeftShoulder","LeftArm","LeftForeArm","LeftHand", 
     "RightShoulder","RightArm","RightForeArm","RightHand", 
     "LeftUpLeg","LeftLeg","LeftFoot","LeftToeBase",
     "RightUpLeg","RightLeg","RightFoot","RightToeBase"
    ]

ee_joints = [
    "LeftHand", "RightHand", "LeftToeBase", "RightToeBase"
    ]

alter_joint_name = {
     "Hips":["Root", "Pelvis", "LowerTorso"], 
     "Spine":["UpperTorso",], 
     "Spine1":["chest",], 
     "Spine2":["chestUpper",], 

     "LeftShoulder": ["LFBXASC032Clavicle", "LeftUpperArm", "shoulder_L",], 
     "LeftArm":["LFBXASC032UpperArm", "LeftLowerArm", "upperArm_L",], 
     "LeftForeArm":["LFBXASC032Forearm", "lowerArm_L"], 
     "LeftHand": ["LFBXASC032Hand", "hand_L"],

     "RightShoulder":["RFBXASC032Clavicle", "RightUpperArm", "shoulder_R",], 
     "RightArm":["RFBXASC032UpperArm", "RightLowerArm", "upperArm_R",], 
     "RightForeArm":["RFBXASC032Forearm", "lowerArm_R"], 
     "RightHand":["RFBXASC032Hand", "hand_R"], 

     "LeftUpLeg":['LFBXASC032Thigh', 'upperLeg_L', 'upperReg_L', 'LeftUpperLeg'],
     "LeftLeg":  ['LFBXASC032Calf',  'lowerLeg_L', 'lowerReg_L', 'LeftLowerLeg'], 
     "LeftFoot":['LFBXASC032Foot', 'foot_L'], 
     "LeftToeBase":['LFBXASC032Toe0', 'toes_L'], 

     "RightUpLeg":['RFBXASC032Thigh', 'upperLeg_R', 'upperReg_R', 'RightUpperLeg'], 
     "RightLeg":  ['RFBXASC032Calf',  'lowerLeg_R', 'lowerReg_R', 'RightLowerLeg'], 
     "RightFoot":['RFBXASC032Foot', 'foot_R'], 
     "RightToeBase":['RFBXASC032Toe0', 'toes_R'], 
    }
