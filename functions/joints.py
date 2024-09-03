# refine joints, hierarchy 
import maya.cmds as cmds

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
    for i, root_joint in enumerate(root_joints):
        hierarchy = get_joint_hierarchy(root_joint)
        hierarchy = refine_joint_name(hierarchy)
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


""" refine hierarchy """
def select_joints(joints, template_joints):
    refined_joints = []
    for template_joint in template_joints:
        for joint in joints:
            alter_joint = joint
            for temp_name, alter_names in alter_joint_name.items():
                changed = False
                for alter_name in alter_names:
                    if joint in alter_name or alter_name in joint:
                        alter_joint = temp_name
                        changed = True
                        break
                if changed:
                    break

            # joint in template joint, not finger
            if (template_joint.lower() in alter_joint.lower() or alter_joint.lower() in template_joint.lower()) and \
                "Thumb" not in joint and \
                "Index" not in joint and \
                "Middle" not in joint and \
                "Ring" not in joint and \
                "Pinky" not in joint:
                refined_joints.append(joint)

                # 체크가 되었으면 joints에서 제거하기
                joints.remove(joint)
                break
        
    return refined_joints

# joint name -> template name (alter)
def refine_joint_name(joints): 
    ret_joints = [] 
    # print("alter_joint_name", alter_joint_name)
    for joint in joints:
        # if joint name in namespace, remove namespace
        if ":" in joint:
            joint = joint.split(":")[-1]

        # print("joint", joint)
        for temp_joint, alter_joints in alter_joint_name.items():
            for alter_joint in alter_joints:
                if joint in alter_joint or alter_joint in joint:
                    joint = temp_joint
                    # print("temp_joint", temp_joint)
                    # 찾았다면 alter joint에서 제거하기 왜 안넣었지? TODO
        ret_joints.append(joint)

    return ret_joints

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
