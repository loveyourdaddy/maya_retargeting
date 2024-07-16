
from functions.joints import *
from functions.keyframe import *
from functions.rotations import *

def retarget_translation(src_hip, tgt_hip, tgt_locator, tgt_locator_rot, tgt_locator_scale):
    # translation
    trans_data, _ = get_keyframe_data(src_hip) 
    trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
    trans_data = get_array_from_keyframe_data(trans_data, trans_attr)
    len_frame = len(trans_data)
    if len_frame != 0:
        if len(tgt_locator)!=0:
            tgt_locator_rot_mat = E_to_R(-1 * np.array(tgt_locator_rot))
        else:
            tgt_locator_rot_mat = np.identity()
        tgt_trans_data = np.einsum('ijk,ik->ij', tgt_locator_rot_mat[None, :].repeat(len_frame, axis=0), trans_data)
        
        # scale translation
        for i in range(3): # x, y, z
            tgt_trans_data[:, i] /= tgt_locator_scale[i]
        
        # update position
        set_keyframe(tgt_hip, tgt_trans_data, trans_attr)

    return trans_data

def retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, tgt_locator_rot,\
                      len_frame,):
    # rotation
    tgt_world_mats = np.full((len_frame, len(tgt_joints), 3, 3), None, dtype=np.float32)
    for j, (src_joint, tgt_joint) in enumerate(zip(src_joints, tgt_joints)):
        # print("{} {} {}".format(j, src_joint, tgt_joint))

        """ src """
        # keyframe_data [attr, frames, (frame, value)]: (trans, world rot)
        _, rot_data = get_keyframe_data(src_joint)

        """ tgt target angle from src """
        # src: world rotation for tgt
        rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
        rot_data = get_array_from_keyframe_data(rot_data, rot_attr)

        """ update data """
        desired_rot_data = np.full((len_frame+1, 3), None, dtype=np.float32)
        for i in range(len_frame):
            """ src """
            # src world angle
            src_local_angle = rot_data[i]
            src_local_mat = E_to_R(src_local_angle)
            
            # src parent angle 
            if j==0:
                # locator
                src_parent_rot_mat = E_to_R(np.array([0,0,0])) # src_locator_rot TODO: src가 다를때 확인 
            else:
                # tgt parent world rot
                src_parent_joint = get_parent_joint(src_joint)
                src_parent_rot_mat = np.transpose(np.array(cmds.xform(src_parent_joint, q=True, ws=True, matrix=True)).reshape(4,4))[:3,:3]
            src_world_mat = src_parent_rot_mat @ src_local_mat

            # target world angle 
            tgt_world_mat = src_world_mat @ Tpose_trfs[j]
            tgt_world_mats[i, j] = tgt_world_mat

            # update by frame
            if j==0:
                # locator
                tgt_parent_rot_mat = E_to_R(np.array(tgt_locator_rot))
            else:
                # tgt parent world rot
                parent_j = parent_indices[j]
                tgt_parent_rot_mat = tgt_world_mats[i, parent_j]
                # if i==0:
                #     print("tgt_parent_rot_mat {}: \n{}".format(parent_j, tgt_parent_rot_mat))
            tgt_local_mat = np.linalg.inv(tgt_parent_rot_mat) @ tgt_world_mat
            tgt_local_angle = R_to_E(tgt_local_mat)
            desired_rot_data[i] = tgt_local_angle

        # update by joint
        set_keyframe(tgt_joint, desired_rot_data, rot_attr)
