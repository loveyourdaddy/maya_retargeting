# retarget 

import maya.mel as mel
from functions.joints import *
from functions.keyframe import *
from functions.rotations import *

def get_rotation_matrix_of_joint(joint):
    rot_mat =  np.transpose(np.array(cmds.xform(joint, q=True, ws=True, matrix=True)).reshape(4,4)[:3,:3])
    return normalize_rotmat(rot_mat)

""" Trf between characters """
def get_Tpose_local_rotations(joints):
    # get Tpose
    Tpose_local_rots = []
    for joint in joints:
        world_rot = get_rotation_matrix_of_joint(joint)

        # parent 
        parent = cmds.listRelatives(joint, parent=True)[0]
        parent_world_rot = get_rotation_matrix_of_joint(parent)

        # local rot 
        local_rot = np.linalg.inv(parent_world_rot) @ world_rot
        Tpose_local_rots.append(local_rot)

    return Tpose_local_rots

def get_Tpose_trf(src_joint_hierarchy, tgt_joint_hierarchy, tgt_prerotations=None):
    # trf: src와 tgt간의 pure rotation 관계

    # world rotation
    Tpose_trfs = []
    for j, (src_joint, tgt_joint) in enumerate(zip(src_joint_hierarchy, tgt_joint_hierarchy)):
        # get rot matrix 
        # print("src {} tgt {}".format(src_joint, tgt_joint))
        src_rot_data = get_rotation_matrix_of_joint(src_joint) 
        tgt_rot_data = get_rotation_matrix_of_joint(tgt_joint)

        trf = np.linalg.inv(src_rot_data) @ tgt_rot_data
        # trf = tgt_rot_data @ np.linalg.inv(src_rot_data)
        Tpose_trfs.append(trf)
    
    return Tpose_trfs

def retarget_translation(src_hip, tgt_hip, 
                         src_locator=None, src_locator_rot=None, src_locator_scale=None,
                         tgt_locator=None, tgt_locator_rot=None, tgt_locator_scale=None, 
                         height_ratio=1):
    # translation data 
    trans_data, _ = get_keyframe_data(src_hip) 
    trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
    trans_data = get_array_from_keyframe_data(trans_data, trans_attr)
    len_frame = len(trans_data)

    # set root position (by locator)
    if len_frame!=0:
        # no locator
        if src_locator==None and tgt_locator==None:
            print(">> no locator")
        # src
        elif src_locator!=None and tgt_locator==None:
            print(">> src locator {} ".format(src_locator))
            src_locator_rot_mat = E_to_R(np.array(src_locator_rot))
            src_locator_rot_mat = src_locator_rot_mat[None, :].repeat(len_frame, axis=0)
            tgt_trans_data = np.einsum('ijk,ik->ij', src_locator_rot_mat, trans_data)
            
            # scale translation
            for i in range(3): # x, y, z
                tgt_trans_data[:, i] *= src_locator_scale[i]
        # tgt
        elif src_locator==None and tgt_locator!=None:
            print(">> tgt locator {} ".format(tgt_locator))
            tgt_locator_rot_mat = E_to_R(-1 * np.array(tgt_locator_rot))
            tgt_locator_rot_mat = tgt_locator_rot_mat[None, :].repeat(len_frame, axis=0)
            tgt_trans_data = np.einsum('ijk,ik->ij', tgt_locator_rot_mat, trans_data)
            
            # scale translation
            for i in range(3): # x, y, z
                tgt_trans_data[:, i] /= tgt_locator_scale[i]
        # both src and tgt
        elif src_locator!=None and tgt_locator!=None:
            print(">> src locator {} tgt locator {}".format(src_locator, tgt_locator))
            # print("before \n", trans_data[0])

            src_locator_rot_mat = E_to_R(np.array(src_locator_rot))
            src_locator_rot_mat = src_locator_rot_mat[None, :].repeat(len_frame, axis=0)

            # tgt_locator_rot_mat = E_to_R(-1 * np.array(tgt_locator_rot))
            tgt_locator_rot_mat = np.linalg.inv(E_to_R(np.array(tgt_locator_rot)))
            tgt_locator_rot_mat = tgt_locator_rot_mat[None, :].repeat(len_frame, axis=0)

            tgt_trans_data = np.einsum('ijk,ik->ij', src_locator_rot_mat, trans_data)
            tgt_trans_data = np.einsum('ijk,ik->ij', tgt_locator_rot_mat, tgt_trans_data)

            # scale translation
            for i in range(3): # x, y, z
                tgt_trans_data[:, i] *= src_locator_scale[i]
                tgt_trans_data[:, i] /= tgt_locator_scale[i]
        else:
            raise ValueError("locator error")

        tgt_trans_data *= height_ratio
        set_keyframe(tgt_hip, tgt_trans_data, trans_attr)

    return trans_data

def retarget_rotation(src_joints, tgt_joints, tgt_joints_all,
                      Tpose_trfs, parent_indices, tgt_Tpose_rots,\
                      len_frame, src_locator_rot=None, tgt_locator_rot=None,\
                        tgt_prerotations=None):
    ''' 
    joint별 처리 
    1. joint가 common_joint에 없다면 world rotation값만 저장
    2. 있다면 local angle을 계산해서 keyframe에 넣어주기 
    '''
    # tgt_prerotations=None

    # rotation data
    src_world_mats = np.full((len_frame, len(tgt_joints), 3, 3), None, dtype=np.float32)
    tgt_world_mats_all = np.full((len_frame, len(tgt_joints_all), 3, 3), None, dtype=np.float32)

    # rotation
    # hand_joints = [9, 28] # TODO: 손 조인트만 뽑기
    for j_all, tgt_joint_all in enumerate(tgt_joints_all):
        ''' all joint '''
        # parent 
        parent_name_all = cmds.listRelatives(tgt_joint_all, parent=True)[0]

        # root인 경우 (parent joint가 locator)
        # tgt_world_mats: I
        if parent_name_all not in tgt_joints_all:
            parent_j_all = None 
            parent_name_all = ''
            tgt_world_mats_all[:, j_all] = np.eye(3)
        # 일반 조인트 
        else:
            parent_j_all = tgt_joints_all.index(parent_name_all)
            parent_name_all = tgt_joints_all[parent_j_all]
        print("{} {}, parent {} {}".format(j_all, tgt_joint_all, parent_j_all, parent_name_all))


        ''' common joint'''
        # index 초기화 
        is_common = False
        j, parent_j, src_joint, tgt_joint = None, None, None, None
        if tgt_joint_all in tgt_joints:
            is_common = True

            j = tgt_joints.index(tgt_joint_all)
            src_joint = src_joints[j]
            tgt_joint = tgt_joints[j]
            parent_j = parent_indices[j]
            parent_name = tgt_joints[parent_j]
            print("     {} {} {}, parent {} {}".format(j, src_joint, tgt_joint, parent_j, parent_name))
            # if j==43:
            #     import pdb; pdb.set_trace()


            # keyframe_data
            # [attr, frames, (frame, value)]: (trans, world rot)
            _, rot_data = get_keyframe_data(src_joint)

            # tgt angle from src
            rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
            rot_data = get_array_from_keyframe_data(rot_data, rot_attr)
            if rot_data.shape[0]!=len_frame:
                print("rot_data {} of joint {} is not matched with len_frame{}".format(rot_data.shape, src_joint, len_frame))
                continue

            # trf
            trf = Tpose_trfs[j]


        ''' update data for frame'''
        tgt_perjoint_local_angle = np.full((len_frame+1, 3), None, dtype=np.float32)
        for i in range(len_frame):
            ''' tgt world '''
            # common joints 
            if is_common:
                """ src world """
                # local angle
                src_local_angle = rot_data[i]
                src_local_mat = E_to_R(src_local_angle)

                # parent angle
                if j==0:
                    if src_locator_rot is not None:
                        src_parent_rot_mat = E_to_R(np.array(src_locator_rot))
                    else:
                        src_parent_rot_mat = E_to_R(np.array([0,0,0]))
                else:
                    # tgt parent world rot
                    src_parent_rot_mat = src_world_mats[i, parent_j]

                # world angle
                src_world_mat = src_parent_rot_mat @ src_local_mat
                src_world_mats[i, j] = src_world_mat

                """ tgt world """
                # world pure rot. world rot = prerot @ pure rot
                tgt_world_mat = src_world_mat @ trf
                tgt_world_mats_all[i, j_all] = tgt_world_mat

            # not common joint 
            else:
                """ tgt world """
                # local 
                tgt_local_mat = tgt_Tpose_rots[j_all]
                # parent world 
                if parent_j_all is None:
                    tgt_parent_world_mat = np.eye(3)
                else:
                    tgt_parent_world_mat = tgt_world_mats_all[i, parent_j_all]
                tgt_world_mat = tgt_parent_world_mat @ tgt_local_mat
                tgt_world_mats_all[i, j_all] = tgt_world_mat
                continue
                # not common joint: end for loop 
            
            
            """ tgt angle """
            # tgt parent world rot
            if j==0:
                # locator
                if tgt_locator_rot is not None:
                    tgt_parent_world_rot = E_to_R(np.array(tgt_locator_rot))
                # src locator, no tgt locator
                else:
                    tgt_parent_world_rot = E_to_R(np.array([0,0,0]))
            else:
                tgt_parent_world_rot = tgt_world_mats_all[i, parent_j_all]

            # local angle
            tgt_local_mat = np.linalg.inv(tgt_parent_world_rot) @ (tgt_world_mat)
            tgt_local_angle = R_to_E(tgt_local_mat)
            tgt_perjoint_local_angle[i] = tgt_local_angle

        # update by joint
        # print("is_common ", is_common)
        if is_common:
            set_keyframe(tgt_joint, tgt_perjoint_local_angle, rot_attr)
