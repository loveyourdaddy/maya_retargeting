# import copy
import maya.cmds as cmds
from functions.joints import *
from functions.keyframe import *
from functions.rotations import *

''' import ''' # move to joints
def get_src_joints(tgt_joints):
    src_joints = cmds.ls(type='joint')
    src_joints = list(set(src_joints) - set(tgt_joints))
    root_joint = find_root_joints(src_joints)
    src_joints = get_joint_hierarchy(root_joint)
    return src_joints

def get_tgt_joints():
    # tgt joint hierarchy
    tgt_joints = cmds.ls(type='joint')
    tgt_root_joint = find_root_joints(tgt_joints)    
    tgt_joints = get_joint_hierarchy(tgt_root_joint)

    return tgt_joints, tgt_root_joint

def get_common_src_tgt_joint_hierarchy(src_joints, tgt_joints, tgt_joints_renamed):
    # refine joint hierarchy
    src_joints, tgt_joints_renamed, parent_indices, _, tgt_indices = get_common_hierarchy_bw_src_and_tgt(src_joints, tgt_joints_renamed, tgt_joints) 

    # tgt_joints
    # refined joint에서 인덱스을 얻을 후, tgt joints에서 뽑기
    tgt_joints = [tgt_joints[i] for i in tgt_indices]

    return src_joints, tgt_joints, tgt_joints_renamed, parent_indices

def get_locator(tgt_locator):
    # get locator 
    tgt_locator = tgt_locator.replace("Shape","")

    # rotation 
    tgt_locator_rot = cmds.xform(tgt_locator, q=True, ws=True, ro=True)
    # scale 
    tgt_locator_scale = cmds.xform(tgt_locator, q=True, ws=True, scale=True)
    # position
    # tgt_locator_pos = cmds.xform(tgt_locator, q=True, ws=True, translation=True)

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
    # Get the list of all nodes in the scene
    all_nodes = cmds.ls(type='transform')

    for node in all_nodes:
        # print(node)
        if cmds.listRelatives(node, children=True)==None and cmds.nodeType(node)!='joint': # mobject.apiType() == om.MFn.kTransform and 
            # Delete the node
            # print(f"Deleted transform node: {node}")
            cmds.delete(node)

def get_distance_from_toe_to_root(joint, root):
    toe = joint[-1] # TODO: find toe joint
    toe_pos = cmds.xform(toe, query=True, translation=True, worldSpace=True)
    root_pos = cmds.xform(root, query=True, translation=True, worldSpace=True)
    
    # 발끝에서 루트까지의 수직 거리를 계산합니다.
    hip_height = root_pos[1] - toe_pos[1]
    return hip_height
