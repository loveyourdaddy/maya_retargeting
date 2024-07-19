import maya.mel as mel
from functions.joints import *
from functions.keyframe import *
from functions.rotations import *

def import_Tpose(sourceChar, targetChar):
    Tpose = "./motions/"+sourceChar+"/T-Pose.fbx"
    # print(Tpose)
    mel.eval('FBXImport -f"{}"'.format(Tpose))

    Tpose = "./motions/"+targetChar+"/T-Pose.fbx"
    # print(Tpose)
    mel.eval('FBXImport -f"{}"'.format(Tpose))

def retarget_translation(src_hip, tgt_hip, tgt_locator=None, tgt_locator_rot=None, tgt_locator_scale=None):
    # translation
    trans_data, _ = get_keyframe_data(src_hip) 
    trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
    trans_data = get_array_from_keyframe_data(trans_data, trans_attr)
    len_frame = len(trans_data)

    # update position
    if len_frame!=0:
        if tgt_locator==None:
            set_keyframe(tgt_hip, trans_data, trans_attr)
        else:
            # if len(tgt_locator)!=0:
            tgt_locator_rot_mat = E_to_R(-1 * np.array(tgt_locator_rot))
            tgt_locator_rot_mat = tgt_locator_rot_mat[None, :].repeat(len_frame, axis=0)
            # else:
            #     tgt_locator_rot_mat = np.identity()
            tgt_trans_data = np.einsum('ijk,ik->ij', tgt_locator_rot_mat, trans_data)
            
            # scale translation
            for i in range(3): # x, y, z
                tgt_trans_data[:, i] /= tgt_locator_scale[i]
            
            # update position
            set_keyframe(tgt_hip, tgt_trans_data, trans_attr)

    return trans_data

def retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, \
                      len_frame, tgt_locator_rot=None):
    # rotation
    # assumtion: src and tgt have same joint names
    src_world_mats = np.full((len_frame, len(tgt_joints), 3, 3), None, dtype=np.float32)
    tgt_world_mats = np.full((len_frame, len(tgt_joints), 3, 3), None, dtype=np.float32)
    for j, (src_joint, tgt_joint) in enumerate(zip(src_joints, tgt_joints)):
        parent_j = parent_indices[j]

        # keyframe_data 
        # [attr, frames, (frame, value)]: (trans, world rot)
        _, rot_data = get_keyframe_data(src_joint)

        # tgt target angle from src
        # src: world rotation for tgt
        rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
        rot_data = get_array_from_keyframe_data(rot_data, rot_attr)

        # update data
        tgt_perjoint_local_angle = np.full((len_frame+1, 3), None, dtype=np.float32)
        for i in range(len_frame):
            """ src """
            # world angle
            src_local_angle = rot_data[i]
            src_local_mat = E_to_R(src_local_angle)
            
            # parent angle 
            if j==0:
                # locator
                src_parent_rot_mat = E_to_R(np.array([0,0,0])) # src_locator_rot TODO: src가 다를때 확인 
            else:
                # tgt parent world rot
                src_parent_rot_mat = src_world_mats[i, parent_j]
            src_world_mat = src_parent_rot_mat @ src_local_mat
            src_world_mats[i, j] = src_world_mat

            """ tgt """
            # world angle 
            tgt_world_mat = src_world_mat @ Tpose_trfs[j]
            tgt_world_mats[i, j] = tgt_world_mat

            # parent world rot
            if j==0:
                # locator
                if tgt_locator_rot is not None:
                    tgt_parent_rotmat = E_to_R(np.array(tgt_locator_rot))
                else:
                    tgt_parent_rotmat = np.identity(3)
            else:
                # tgt parent world rot
                tgt_parent_rotmat = tgt_world_mats[i, parent_j]

            # update by frame
            tgt_local_mat = np.linalg.inv(tgt_parent_rotmat) @ tgt_world_mat
            tgt_local_angle = R_to_E(tgt_local_mat)
            tgt_perjoint_local_angle[i] = tgt_local_angle

        # update by joint
        set_keyframe(tgt_joint, tgt_perjoint_local_angle, rot_attr)
