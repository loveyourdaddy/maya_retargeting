import maya.mel as mel
from functions.joints import *
from functions.keyframe import *
from functions.rotations import *

def get_worldrot_of_joint(joint):
    rot_mat =  np.transpose(np.array(cmds.xform(joint, q=True, ws=True, matrix=True)).reshape(4,4)[:3,:3])
    return normalize_rotmat(rot_mat)

def get_localrot_of_joint(joint):
    rot_mat = np.transpose(np.array(cmds.xform(joint, q=True, ws=False, matrix=True)).reshape(4,4)[:3,:3])
    return normalize_rotmat(rot_mat)

def get_Tpose_local_rotations(joints):
    # get Tpose
    Tpose_local_rots = []
    for joint in joints:
        world_rot = get_worldrot_of_joint(joint)

        # parent 
        parent = cmds.listRelatives(joint, parent=True)[0]
        parent_world_rot = get_worldrot_of_joint(parent)

        # local rot 
        local_rot = np.linalg.inv(parent_world_rot) @ world_rot
        Tpose_local_rots.append(local_rot)

    return Tpose_local_rots

def mmatrix_to_numpy(mmatrix):
    values = []
    for row in range(4): # 4x4 행렬 순회
        for col in range(4):
            values.append(mmatrix(row, col))  # 각 요소 추가
    return np.array(values).reshape(4, 4)  # numpy 배열로 변환 후 4x4 형태로 reshape

def get_Tpose_localrot(joints):
    cmds.currentTime(0)

    Tpose_local_rots = []
    for j, joint in enumerate(joints):
        rot = cmds.getAttr(f"{joint}.rotate")[0]
        Tpose_local_rots.append(rot)

    return Tpose_local_rots
