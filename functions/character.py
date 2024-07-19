import copy
import maya.cmds as cmds

from functions.joints import *
from functions.keyframe import *
from functions.rotations import *

def get_tgt_joints():
    # tgt joint hierarchy
    tgt_joints = cmds.ls(type='joint')
    tgt_root_joint = find_root_joints(tgt_joints)
    tgt_joints = get_joint_hierarchy(tgt_root_joint)
    tgt_joints = select_joints(tgt_joints, template_joints)

    return tgt_joints, tgt_root_joint

def get_locator(tgt_locator):
    # get locator 
    tgt_locator = tgt_locator[0].replace("Shape","")

    # rotation 
    tgt_locator_rot = cmds.xform(tgt_locator, q=True, ws=True, ro=True)
    # position
    # tgt_locator_pos = cmds.xform(tgt_locator, q=True, ws=True, translation=True)
    # scale 
    tgt_locator_scale = cmds.xform(tgt_locator, q=True, ws=True, scale=True)
    # set locator 
    # cmds.xform(tgt_locator, q=False, ws=True, translation=tgt_locator_pos)

    return tgt_locator, tgt_locator_rot, tgt_locator_scale


def get_src_joints(tgt_joints):
    # refine joint hierarchy
    src_joints = cmds.ls(type='joint')
    src_joints = list(set(src_joints) - set(tgt_joints))
    root_joint = find_root_joints(src_joints)
    src_joint_hierarchy = get_joint_hierarchy(root_joint)
    src_joint_hierarchy = select_joints(src_joint_hierarchy, template_joints)

    return src_joint_hierarchy

def refine_joints(src_joint_hierarchy, tgt_joint_hierarchy):
    # Original name

    # find common joints 
    src_common_joint = []
    tgt_common_joint = []
    src_indices = []
    tgt_indices = []
    for src_idx, src_joint in enumerate(src_joint_hierarchy):
        check = False
        for tgt_idx, tgt_joint in enumerate(tgt_joint_hierarchy):
            # find common joint 
            if src_joint.lower() in tgt_joint.lower() or tgt_joint.lower() in src_joint.lower():
                src_common_joint.append(src_joint)
                tgt_common_joint.append(tgt_joint)
                src_indices.append(src_idx)
                tgt_indices.append(tgt_idx)
                check = True 
                break
        if check:
            continue

    # selected joint hierarchy
    src_select_hierarchy, tgt_select_hierarchy = [], []
    name2index = {}
    index2name = {}
    for i in range(len(src_indices)):
        name = src_joint_hierarchy[src_indices[i]]
        src_select_hierarchy.append(name)
        tgt_select_hierarchy.append(tgt_joint_hierarchy[tgt_indices[i]])
        name2index[name] = i
        index2name[i] = name
    src_joint_hierarchy = src_select_hierarchy
    tgt_joint_hierarchy = tgt_select_hierarchy

    # parent index
    parent_indices = []
    division = []
    child_of_divisions = []
    for i in range(len(src_indices)):
        # if num child>0, parent joint 
        joint_name = src_joint_hierarchy[src_indices[i]]
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

        # divider
        if children is not None and len(children)>1 and tgt_joint_hierarchy[i] not in ee_joints: # joint name is not in end effector 
            division_j = copy.deepcopy(i)
            division.append(division_j)
            child_of_divisions.append(children_index)
        
    return src_joint_hierarchy, tgt_joint_hierarchy, parent_indices, src_indices, tgt_indices

def get_Tpose_trf(src_joint_hierarchy, tgt_joint_hierarchy):
    # world rotation
    Tpose_trfs = []
    for j, (src_joint, tgt_joint) in enumerate(zip(src_joint_hierarchy, tgt_joint_hierarchy)):
        src_rot_data = np.transpose(np.array(cmds.xform(src_joint, q=True, ws=True, matrix=True)).reshape(4,4)[:3,:3])
        tgt_rot_data = np.transpose(np.array(cmds.xform(tgt_joint, q=True, ws=True, matrix=True)).reshape(4,4)[:3,:3])
        trf = np.linalg.inv(src_rot_data) @ tgt_rot_data
        Tpose_trfs.append(trf)
    
    return Tpose_trfs
