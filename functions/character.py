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
    tgt_locator = tgt_locator[0].replace("Shape","")

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

""" Get prerot """
def get_prerotations(tgt_joints, tgt_locator=None, tgt_locator_rot=None):
    # (locator, joint들의) local rotation을 저장 후 나중에 복원.
    angle_origins = []
    prerotations = []
    if tgt_locator is not None:
        cmds.xform(tgt_locator, ro=(0,0,0), q=False, ws=False)
    for j, joint in enumerate(tgt_joints):
        # zero rotation을 만들어야하는게 아닐까?
        angle_origin = cmds.xform(joint, q=True, ws=False, ro=True)
        angle_origins.append(angle_origin)

        # set zero rot and get world rot 
        cmds.xform(joint, ro=(0,0,0), q=False, ws=False)
        prerot = np.transpose(np.array(cmds.xform(joint, q=True, ws=True, matrix=True)).reshape(4,4)[:3,:3])
        prerotations.append(prerot)

    # 기존 값으로 돌려주기
    if tgt_locator is not None:
        cmds.xform(tgt_locator, ro=(tgt_locator_rot), q=False, ws=False)
    for j, joint in enumerate(tgt_joints):
        angle_origin = angle_origins[j]
        cmds.xform(joint, ro=tuple(angle_origin), q=False, ws=False)
    
    return prerotations
