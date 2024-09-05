# import and delete the part of character (joints, locator, meshes)
import copy
import maya.cmds as cmds

from functions.joints import *
from functions.keyframe import *
from functions.rotations import *

''' import '''
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

def get_joint_hierarchy_and_Tpose_trf(tgt_joints, tgt_joints_refined):
    from functions.motion import get_Tpose_trf

    # get src, tgt, joint hierarchy, Tpose trf
    src_joints = get_src_joints(tgt_joints)

    # refine name
    src_joints, tgt_joints_refined, parent_indices, _, tgt_indices = refine_joints(src_joints, tgt_joints_refined, tgt_joints) 

    # tgt_joints
    # refined joint에서 인덱스을 얻을 후, tgt joints에서 뽑기
    tgt_joints = [tgt_joints[i] for i in tgt_indices]

    # Tpose trf
    Tpose_trfs = get_Tpose_trf(src_joints, tgt_joints)

    return src_joints, tgt_joints, tgt_joints_refined, parent_indices, Tpose_trfs


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

''' delete '''
def delete_locator_and_hierarchy(locator_name):
    if cmds.objExists(locator_name):
        # List all descendants of the locator
        descendants = cmds.listRelatives(locator_name, allDescendents=True) or []
        
        # Add the locator itself to the list
        descendants.append(locator_name)
        
        # Delete the locator and its hierarchy
        cmds.delete(descendants)
        # print(f"{locator_name} and its hierarchy have been deleted.")
    else:
        pass
        # print(f"{locator_name} does not exist.")

def delete_all_transform_nodes():
    # import maya.OpenMaya as om
    # Get the list of all nodes in the scene
    all_nodes = cmds.ls(type='transform')
    # print("all_nodes", all_nodes)

    for node in all_nodes:
        # print(node)
        if cmds.listRelatives(node, children=True)==None and cmds.nodeType(node)!='joint': # mobject.apiType() == om.MFn.kTransform and 
            # Delete the node
            # print(f"Deleted transform node: {node}")
            cmds.delete(node)

''' refine '''
def refine_joints(src_joint_hierarchy, tgt_joint_hierarchy, tgt_joint_hierarchy_origin):
    # find common joints 
    src_common_joint = []
    tgt_common_joint = []
    src_indices = []
    tgt_indices = []

    # get division 
    def get_spine_division(joint_hierarchy):
        division = []
        for i, joint_name in enumerate(joint_hierarchy):
            children = cmds.listRelatives(joint_name, children=True, type='joint')
            if children is not None and len(children)>1 and src_joint_hierarchy[i]:
                division.append(joint_name)
                if len(division)==2:
                    return i, joint_name
        raise ValueError("division not found")
    
    src_spine_div_jid, src_spine_div = get_spine_division(src_joint_hierarchy)
    tgt_spine_div_jid, tgt_spine_div = get_spine_division(tgt_joint_hierarchy_origin)
    src_spine_div = src_spine_div.split(':')[-1]
    tgt_spine_div = tgt_spine_div.split(':')[-1]


    # find common joints 
    # src_spine_check_flag = False
    # tgt_spine_check_flag = False

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
                print("src {} tgt {}".format(src_joint, tgt_joint))
                # add spine division
                # 만약 joint가 spine div조인트를 넘어갔다면, check spine joint in src common joint. # 없다면 마지막 조인트를 1개 빼주고(spine이 1개는 있다고 가정.) division joint을 넣어주기
                if spine_check_flag==False and src_idx > src_spine_div_jid and tgt_idx > tgt_spine_div_jid:
                    # import pdb; pdb.set_trace()
                    if src_joint not in src_common_joint:
                        src_common_joint[-1] = src_spine_div
                        src_indices[-1] = src_spine_div_jid
                    if tgt_joint not in tgt_common_joint:
                        tgt_common_joint[-1] = tgt_spine_div
                        tgt_indices[-1] = tgt_spine_div_jid
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
        joint_name = joint_hierarchy[i] # joint_indices[i]
        print("{} {}".format(i, joint_name))

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
