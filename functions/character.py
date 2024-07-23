import copy
import maya.cmds as cmds

from functions.joints import *
from functions.keyframe import *
from functions.rotations import *


def get_src_joints(tgt_joints):
    src_joints = cmds.ls(type='joint')
    src_joints = list(set(src_joints) - set(tgt_joints))
    root_joint = find_root_joints(src_joints)
    src_joint_hierarchy = get_joint_hierarchy(root_joint)
    # refine joint hierarchy
    src_joint_hierarchy = select_joints(src_joint_hierarchy, template_joints)

    return src_joint_hierarchy

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

def refine_joints(src_joint_hierarchy, tgt_joint_hierarchy, tgt_joint_hierarchy_origin):
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


    # parent index
    parent_indices = []
    division = []
    child_of_divisions = []
    # print("src {} {} \ntgt {} {}".format(len(src_joint_hierarchy), src_joint_hierarchy, len(tgt_joint_hierarchy_origin), tgt_joint_hierarchy_origin))
    # 적은것 기준
    if len(src_indices) < len(tgt_indices):
        joint_indices = src_indices
        joint_hierarchy = src_joint_hierarchy
        name2index = src_name2index
        print("src standard")
    else:
        joint_indices = tgt_indices
        joint_hierarchy = tgt_joint_hierarchy_origin
        name2index = tgt_name2index
        print("tgt standard")

    for i in range(len(joint_indices)):
        joint_name = joint_hierarchy[joint_indices[i]]

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

        # divider
        # children이 있고, end effector가 아닌 경우
        if children is not None and len(children)>1 and joint_hierarchy[i] not in ee_joints:
            division_j = copy.deepcopy(i)
            division.append(division_j)
            child_of_divisions.append(children_index)
    
    return src_joint_hierarchy, tgt_joint_hierarchy, parent_indices, src_indices, tgt_indices
