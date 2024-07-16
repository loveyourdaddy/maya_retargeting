import maya.cmds as cmds

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
    
    for joint in all_joints:
        parents = cmds.listRelatives(joint, parent=True)
        
        if not parents or cmds.nodeType(parents[0]) != 'joint': 
            root_joints.append(joint)
    
    return root_joints[0] # should be one 

def select_joints(joints, template_joints):
    refined_joints = []
    for template_joint in template_joints:
        for joint in joints:
            # find alternative name 
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
                break
        
    return refined_joints

def refine_joint_name(joints):
    ret_joints = [] 
    for joint in joints:
        # replace joint name as template name
        for temp_joint, alter_joints in alter_joint_name.items():
            for alter_joint in alter_joints:
                if joint in alter_joint or alter_joint in joint:
                    joint = temp_joint
        ret_joints.append(joint)

    return ret_joints

def get_parent_joint(joint):
    parent = cmds.listRelatives(joint, parent=True)
    if parent:
        return parent[0]
    else:
        return None
    
def get_top_level_nodes():
    return cmds.ls(assemblies=True)

# joints
template_joints = [
    "Hips","Spine","Spine1","Spine2",
     "Neck","Head", 
     "LeftShoulder","LeftArm","LeftForeArm","LeftHand", 
     "RightShoulder","RightArm","RightForeArm","RightHand", 
     "LeftUpLeg","LeftLeg","LeftFoot","LeftToeBase",
     "RightUpLeg","RightLeg","RightFoot","RightToeBase"]
    # 22 = 4+2+4+4+4+4

ee_joints = [
    "LeftHand", "RightHand", "LeftToeBase", "RightToeBase"
]

alter_joint_name = {
     "Hips":["Pelvis", "LowerTorso"], 
     "Spine":["UpperTorso",],

     "LeftShoulder": ["LFBXASC032Clavicle", "LeftUpperArm"], 
     "LeftArm":["LFBXASC032UpperArm", "LeftLowerArm"], 
     "LeftForeArm":["LFBXASC032Forearm"], 
     "LeftHand": ["LFBXASC032Hand"],

     "RightShoulder":["RFBXASC032Clavicle", "RightUpperArm"], 
     "RightArm":["RFBXASC032UpperArm", "LeftUpperArm"], 
     "RightForeArm":["RFBXASC032Forearm"], 
     "RightHand":["RFBXASC032Hand"], 

     "LeftUpLeg":['LFBXASC032Thigh'], 
     "LeftLeg":['LFBXASC032Calf'], 
     "LeftFoot":['LFBXASC032Foot'], 
     "LeftToeBase":['LFBXASC032Toe0'], 

     "RightUpLeg":['RFBXASC032Thigh'], 
     "RightLeg":['RFBXASC032Calf'], 
     "RightFoot":['RFBXASC032Foot'], 
     "RightToeBase":['RFBXASC032Toe0'], 
    }

