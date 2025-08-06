# refine joints, hierarchy 
import maya.cmds as cmds
import copy
import numpy as np
from functions.rotations import normalize_rotmat

# Template joints
# joints
# Hip1 + Spine5 + Head2 + RightArm4 + LeftArm4 + LeftLeg4 + RightLeg4 = 24
alter_joint_name = {
    "Hips":["Root", "Pelvis", "LowerTorso", "Bone"], 
    "Spine":["UpperTorso", 'spine'], 
    "Spine1":["spine_1", "spine_02"], # TODO: spine_02 제거
    "Spine2":["chest", "spine_2", "spine_03"], # "chestUpper", 
    "Spine3":["chestUpper", "spine_3", "spine_04"], 
    "Spine4":["chestUpper", "spine_4", "spine_05", "BoneFBXASC046001"], 

    "Neck":["neck", "neck_01", "BoneFBXASC046006"], 
    "Neck1":["neck1", "neck_02",], # TODO: neck_02 제거
    # "Neck":["neck_01", "BoneFBXASC046006"], 
    "Head":["head",], 

    "RightShoulder":["RFBXASC032Clavicle", "Clavicle_r", "shoulder_R", ],
    "RightArm":["RFBXASC032UpperArm",  "RightUpperArm", "upperArm_R", "BoneFBXASC046005"], # 5, 6
    "RightForeArm":["RFBXASC032Forearm", "RightForearm", "RightLowerArm",  "lowerArm_R", ], # "BoneFBXASC046005" "lowerarm_in_r", 
    "RightHand":["RFBXASC032Hand", "RightHand", "hand_R", "BoneFBXASC046006"], # "lowerarm_out_r", 

    "LeftShoulder": ["LFBXASC032Clavicle", "Clavicle_l", "shoulder_L", ],
    "LeftArm":["LFBXASC032UpperArm", "LeftUpperArm", "upperArm_L", "BoneFBXASC046003"], # 3,4
    "LeftForeArm":["LFBXASC032Forearm", "LeftForearm", "LeftLowerArm", "lowerArm_L", ], # "BoneFBXASC046003" "lowerarm_in_l", 
    "LeftHand": ["LFBXASC032Hand", "LeftHand", "hand_L", "BoneFBXASC046004"], # "lowerarm_out_l", 

    "RightUpLeg":['RFBXASC032Thigh', 'upperLeg_R', 'upperReg_R', 'RightUpperLeg', 'thigh_r', "BoneFBXASC046007"], # 7 8
    "RightLeg":  ['RFBXASC032Calf',  'lowerLeg_R', 'lowerReg_R', 'RightLowerLeg', 'calf_r'], 
    "RightFoot":['RFBXASC032Foot', 'foot_R', "BoneFBXASC046008"], 
    "RightToeBase":['RFBXASC032Toe0', 'toes_R', 'ball_r'], 

    "LeftUpLeg":['LFBXASC032Thigh', 'upperLeg_L', 'upperReg_L', 'LeftUpperLeg', 'thigh_l', "BoneFBXASC046009"], # 9 10
    "LeftLeg":  ['LFBXASC032Calf',  'lowerLeg_L', 'lowerReg_L', 'LeftLowerLeg', 'calf_l', ], 
    "LeftFoot":['LFBXASC032Foot', 'foot_L', "BoneFBXASC046010", ], 
    "LeftToeBase":['LFBXASC032Toe0', 'toes_L', "ball_l"], 
    }

finger_alter_joint_name = {
    # finger 
    "LeftHandThumb1":["LeftHandThumb1", "Thumb_01_l", "thumbPro_L"], 
    "LeftHandThumb2":["LeftHandThumb2", "Thumb_02_l", "thumbInt_L"], 
    "LeftHandThumb3":["LeftHandThumb3", "Thumb_03_l", "thumbDis_L"], 
    "LeftHandIndex1":["LeftHandIndex1", "Index_01_l", "indexPro_L"], 
    "LeftHandIndex2":["LeftHandIndex2", "Index_02_l", "indexInt_L"], 
    "LeftHandIndex3":["LeftHandIndex3", "Index_03_l", "indexDis_L"], 
    "LeftHandMiddle1":["LeftHandMiddle1", "Middle_01_l", "middlePro_L"], 
    "LeftHandMiddle2":["LeftHandMiddle2", "Middle_02_l", "middleInt_L"], 
    "LeftHandMiddle3":["LeftHandMiddle3", "Middle_03_l", "middleDis_L"], 
    "LeftHandRing1":["LeftHandRing1", "Ring_01_l", "ringPro_L"], 
    "LeftHandRing2":["LeftHandRing2", "Ring_02_l", "ringInt_L"], 
    "LeftHandRing3":["LeftHandRing3", "Ring_03_l", "ringDis_L"], 
    "LeftHandPinky1":["LeftHandPinky1", "Pinky_01_l", "littlePro_L"], 
    "LeftHandPinky2":["LeftHandPinky2", "Pinky_02_l", "littleInt_L"], 
    "LeftHandPinky3":["LeftHandPinky3", "Pinky_03_l", "littleDis_L"], 

    # right hand
    "RightHandThumb1":["RightHandThumb1",   "Thumb_01_r",  "thumbPro_R"],
    "RightHandThumb2":["RightHandThumb2",   "Thumb_02_r",  "thumbInt_R"],
    "RightHandThumb3":["RightHandThumb3",   "Thumb_03_r",  "thumbDis_R"],
    "RightHandIndex1":["RightHandIndex1",   "Index_01_r",  "indexPro_R"],
    "RightHandIndex2":["RightHandIndex2",   "Index_02_r",  "indexInt_R"],
    "RightHandIndex3":["RightHandIndex3",   "Index_03_r",  "indexDis_R"],
    "RightHandMiddle1":["RightHandMiddle1", "Middle_01_r", "middlePro_R"],
    "RightHandMiddle2":["RightHandMiddle2", "Middle_02_r", "middleInt_R"],
    "RightHandMiddle3":["RightHandMiddle3", "Middle_03_r", "middleDis_R"],
    "RightHandRing1":["RightHandRing1",     "Ring_01_r",   "ringPro_R"],
    "RightHandRing2":["RightHandRing2",     "Ring_02_r",   "ringInt_R"],
    "RightHandRing3":["RightHandRing3",     "Ring_03_r",   "ringDis_R"],
    "RightHandPinky1":["RightHandPinky1",   "Pinky_01_r",  "littlePro_R"],
    "RightHandPinky2":["RightHandPinky2",   "Pinky_02_r",  "littleInt_R"],
    "RightHandPinky3":["RightHandPinky3",   "Pinky_03_r",  "littleDis_R"],
}

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
        # print("joint {}, parents {}".format(joint, parents))

        # parent가 없거나, parent가 joint가 아니면, root joint에 추가
        if not parents or (cmds.nodeType(parents[0]) != 'joint'):
            root_joints.append(joint)

    # find best root joint: 
    children_of_roots = [[] for _ in range(len(root_joints))]
    list_index = []
    for i, root_joint in enumerate(root_joints):
        hierarchy = get_joint_hierarchy(root_joint)
        hierarchy, _, _ = rename_joint_by_template(hierarchy)
        children_of_roots[i] = select_joints_by_template(hierarchy)
        list_index.append(len(children_of_roots[i]))
    
    max_index = list_index.index(max(list_index))
    return max_index, root_joints

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
    key_list = list(alter_joint_name.keys())

    ret_joints = []
    input_jids_in_template = []
    template_indices_for_input_joints = []
    for jid, joint in enumerate(joints):
        # if joint name in namespace, remove namespace
        if ":" in joint:
            joint = joint.split(":")[-1]

        # replace joint name to template key name
        check = False
        for key_joint, alter_joints in alter_joint_name.items():
            for alter_joint in alter_joints:
                # list 안에 있고, 이미 등록되지 않다면
                if (joint.lower() in alter_joint.lower() or alter_joint.lower() in joint.lower()) and key_joint not in ret_joints:
                    # template joint가 맞다면,
                    joint = key_joint
                    
                    # template joint indices에 넣어주고
                    input_jids_in_template.append(jid)
                    
                    # 입력에 대한 template indices을 업데이트 해주기 
                    template_index = key_list.index(key_joint)
                    template_indices_for_input_joints.append(template_index)
                    # print(f"key_joint {key_joint} template_index {template_index}")

                    # 다음 tempalte으로 넘어가기 
                    template_index += 1
                    check = True
                    break
            if check:
                break

        # print("{} joint {} -> {}".format(jid, joints[jid], joint))
        # template joint가 아니라면, -1
        if check==False:
            template_indices_for_input_joints.append(-1)
        
        # finger 조인트: finger_포함하기
        if check==False:
            for key_joint, alter_joints in finger_alter_joint_name.items():
                for alter_joint in alter_joints:
                    # list 안에 있고, 이미 등록되지 않다면
                    if (joint.lower() in alter_joint.lower() or alter_joint.lower() in joint.lower()) and key_joint not in ret_joints:
                        joint = "finger_"+key_joint
                    
        ret_joints.append(joint)

    return ret_joints, input_jids_in_template, template_indices_for_input_joints

""" Root """
# find root joint index
def get_root_joint(joints_common):
    hip_index = 0
    for i, joint in enumerate(joints_common):
        if joint.lower().find("hips") != -1:
            hip_index = i
            continue
        if joint.lower().find("spine") != -1:
            break
    return hip_index

""" refine hierarchy """
# select body skeleton (not finger) 
def select_joints_by_template(joints):
    refined_joints = []
    added_template_joints = []
    alter_joint_name_ = copy.deepcopy(alter_joint_name)
    template_joints = list(alter_joint_name.keys()) 
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
        if cmds.objExists(joint):
            new_joints.append(add_namespace(joint, namespace))
        else:
            new_joints.append(namespace + ':' + joint)
    return new_joints

def add_namespace_for_meshes(meshes, namespace):
    if not cmds.namespace(exists=namespace):
        cmds.namespace(add=namespace)
    existing_namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
    print("현재 존재하는 네임스페이스:", existing_namespaces)
    if namespace not in existing_namespaces:
        print(f"add {namespace} namespace")
        cmds.namespace(add=namespace)

    new_meshes = []
    for mesh in meshes:
        if not cmds.objExists(mesh):
            # new_meshes.append(mesh)
            continue
        transform = cmds.listRelatives(mesh, parent=True)[0]
        short_name = transform.split('|')[-1]
        
        # 이미 네임스페이스가 있는지 확인
        if ':' in short_name:
            base_name = short_name.split(':')[-1]
        else:
            base_name = short_name

        # 새 이름 생성
        new_name = f"{namespace}:{base_name}"
        
        # 조인트를 src 네임스페이스로 이동
        renamed_transform = cmds.rename(transform, new_name)

        renamed_mesh = cmds.listRelatives(renamed_transform, shapes=True)[0]
        new_meshes.append(renamed_mesh)

    return new_meshes

def remove_namespace_from_objects(objects):
    """
    모든 오브젝트에서 네임스페이스를 제거합니다.
    """
    new_objects = []
    
    for obj in objects:
        # 전체 경로에서 짧은 이름 추출
        short_name = obj.split('|')[-1]
        
        # 네임스페이스가 있는지 확인
        if ':' in short_name:
            # 네임스페이스 없이 기본 이름만 가져오기
            base_name = short_name.split(':')[-1]
            
            # 오브젝트 이름 변경
            renamed = cmds.rename(obj, base_name)
            # print("Object {} -> {}".format(obj, renamed))
            new_objects.append(renamed)
        else:
            # 이미 네임스페이스가 없으면 그대로 추가
            new_objects.append(obj)
            
    return new_objects

def remove_transform_node(obj):
    transform_nodes = []
    # 부모 변형 노드 찾기
    parents = cmds.listRelatives(obj, parent=True)
    if parents:
        transform_nodes.extend(parents)

    # 중복 제거
    transform_nodes = list(set(transform_nodes))

    # 변형 노드 삭제 (자식 메시 노드도 함께 삭제됨)
    cmds.delete(transform_nodes)

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
def get_prerotations(tgt_joints, tgt_joints_origin, tgt_locator=None, tgt_locator_rot=None):
    # (locator, joint들의) local rotation을 저장 후 나중에 복원.

    # set zero 
    if tgt_locator is not None:
        cmds.xform(tgt_locator, ro=(0,0,0), q=False, ws=False)
    # set zero rotation for every joints 
    angle_origins = []
    for joint in tgt_joints_origin:
        # get angle 
        angle_origin = cmds.xform(joint, q=True, ws=False, ro=True)
        angle_origins.append(angle_origin)
        # set zero 
        cmds.xform(joint, ro=(0,0,0), q=False, ws=False)

    # get prerot
    prerotations = []
    for j, joint in enumerate(tgt_joints):
        # set zero rot and get world rot 
        cmds.xform(joint, ro=(0,0,0), q=False, ws=False)
        prerot = np.transpose(np.array(cmds.xform(joint, q=True, ws=True, matrix=True)).reshape(4,4))[:3,:3]
        prerot = normalize_rotmat(prerot)
        prerotations.append(prerot)
        # print(f"joint {j} {joint} angle {angle_origin} prerot \n{prerot}")

    # 기존 값으로 돌려주기
    if tgt_locator is not None:
        cmds.xform(tgt_locator, ro=(tgt_locator_rot), q=False, ws=False)
    for j, joint in enumerate(tgt_joints_origin): # tgt_joints
        angle_origin = angle_origins[j]
        cmds.xform(joint, ro=tuple(angle_origin), q=False, ws=False)

    return prerotations
