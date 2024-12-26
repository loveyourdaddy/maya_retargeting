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


def rename_duplicate_joints():
    """
    씬에서 중복된 조인트 이름을 찾아서 새로운 이름으로 변경합니다.
    새 이름은 원본 이름 뒤에 숫자를 붙여서 생성됩니다.
    """
    # 씬의 모든 조인트를 가져옵니다
    all_joints = cmds.ls(type='joint', long=True)
    
    # 조인트의 짧은 이름을 저장할 딕셔너리
    joint_names = {}
    
    # 중복 이름을 찾습니다
    duplicates = []
    for joint in all_joints:
        # 전체 경로에서 짧은 이름만 추출
        short_name = joint.split('|')[-1]
        
        if short_name in joint_names:
            # 중복된 이름이 발견되면 리스트에 추가
            duplicates.append(joint)
        else:
            joint_names[short_name] = joint
    
    # 중복된 조인트들의 이름을 변경합니다 (중복된 조인트 중 뒤의 조인트)
    for duplicate in duplicates:
        short_name = duplicate.split('|')[-1]
        counter = 1
        
        # 새로운 이름이 고유할 때까지 숫자를 증가시킵니다
        while True:
            new_name = f"{short_name}_{counter}"
            if not cmds.objExists(new_name):
                # 이름 변경 실행
                if cmds.objExists(duplicate):
                    cmds.rename(duplicate, new_name)
                    # print("Duplicated renamed: {} -> {}".format(duplicate, new_name))
                    break
                if cmds.objExists(short_name):
                    # 일단 2개로 가정.
                    # print("joint {} has {} same joints".format(short_name, len(cmds.ls(short_name, long=True))))

                    long_name = cmds.ls(short_name, long=True)[-1]
                    cmds.rename(long_name, new_name)
                    # print("Shortname renamed: {} -> {}".format(short_name, new_name))
                    break

            counter += 1


def get_tgt_joints():
    # 조인트의 이름이 겹칠때 1, 2을 추가해주기
    rename_duplicate_joints()

    # tgt joint hierarchy
    tgt_joints = cmds.ls(type='joint')

    # add namespace joints (in maya also)
    tgt_joints = add_namespace_for_joints(tgt_joints, "tgt")

    # root joint
    tgt_root_joint = find_root_joints(tgt_joints)
    tgt_joints = get_joint_hierarchy(tgt_root_joint)

    return tgt_joints, tgt_root_joint

def get_common_src_tgt_joint_hierarchy(src_joints_origin, src_joints_template, tgt_joints_origin, tgt_joints_template):
    # refine joint hierarchy
    src_joints_template, tgt_joints_template, parent_indices, src_indices, tgt_indices,\
        = get_common_hierarchy_bw_src_and_tgt(src_joints_origin, src_joints_template, tgt_joints_origin, tgt_joints_template)

    # templated: refined joint에서 인덱스을 얻을 후, tgt joints에서 뽑기
    src_joints_templated = [src_joints_origin[i] for i in src_indices]
    tgt_joints_templated = [tgt_joints_origin[i] for i in tgt_indices]

    return src_joints_templated, tgt_joints_templated, src_indices, tgt_indices, parent_indices #, src_common_joint, tgt_common_joint

def get_locator(tgt_locator):
    # get locator 
    tgt_locator = tgt_locator.replace("Shape","")

    # rotation 
    tgt_locator_rot = cmds.xform(tgt_locator, q=True, ws=True, ro=True)
    # scale 
    tgt_locator_scale = cmds.xform(tgt_locator, q=True, ws=True, scale=True)
    # position
    tgt_locator_pos = cmds.xform(tgt_locator, q=True, ws=True, translation=True)

    return tgt_locator, tgt_locator_rot, tgt_locator_scale, tgt_locator_pos

''' delete '''
def delete_locator_and_hierarchy(locator_name):
    if cmds.objExists(locator_name):
        # List all descendants of the locator
        descendants = cmds.listRelatives(locator_name, allDescendents=True) or []
        
        # Add the locator itself to the list
        descendants.append(locator_name)
        # import pdb; pdb.set_trace()
        
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
