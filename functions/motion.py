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

def retarget_rotation(src_joints, tgt_joints, src_joints_origin, tgt_joints_origin,
                      Tpose_trfs, parent_indices, 
                      src_Tpose_rots, tgt_Tpose_rots,\
                      len_frame, src_locator_rot=None, tgt_locator_rot=None,\
                        tgt_prerotations=None):
    ''' 
    joint별 처리 
    1. joint가 common_joint에 없다면 world rotation값만 저장
    2. 있다면 local angle을 계산해서 keyframe에 넣어주기 
    '''

    # rotation data
    ''' src world rot '''
    # src_world_mats_origin = np.full((len_frame, len(src_joints_origin), 3, 3), None, dtype=np.float32)
    src_world_mats_origin = np.eye(3)[None, None, :, :].repeat(len_frame, axis=0).repeat(len(src_joints_origin), axis=1)
    for src_j_origin, src_joint_origin in enumerate(src_joints_origin):
        is_common = False
        if src_joint_origin in src_joints:
            is_common = True 

            # joint index
            j = src_joints.index(src_joint_origin)
            src_joint = src_joints[j]
                
            # keyframe_data
            # [attr, frames, (frame, value)]: (trans, world rot)
            _, rot_data = get_keyframe_data(src_joint)

            # tgt angle from src
            rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
            rot_data = get_array_from_keyframe_data(rot_data, rot_attr)
            if rot_data.shape[0]!=len_frame:
                print("rot_data {} of joint {} is not matched with len_frame{}".format(rot_data.shape, src_joint, len_frame))
                continue

        # parent joint 
        src_parent_name_origin = cmds.listRelatives(src_joint_origin, parent=True)[0]
        if src_parent_name_origin not in src_joints_origin:
            src_parent_j_origin = None
        else:
            src_parent_j_origin = src_joints_origin.index(src_parent_name_origin)

        # world rot for frames
        for i in range(len_frame):
            # common일때는 parent joint을 받아서 world rot 계산 
            if is_common:
                """ src world """
                # local angle
                src_local_angle = rot_data[i]
                src_local_mat = E_to_R(src_local_angle)
                
                if src_j_origin==0:
                    if src_locator_rot is not None:
                        src_parent_rot_mat = E_to_R(np.array(src_locator_rot))
                    else:
                        src_parent_rot_mat = E_to_R(np.array([0,0,0]))
                else:
                    # tgt parent world rot
                    src_parent_rot_mat = src_world_mats_origin[i, src_parent_j_origin]

                # world angle
                src_world_mat = src_parent_rot_mat @ src_local_mat
                src_world_mats_origin[i, src_j_origin] = src_world_mat

            # common이 아닐때에는 parent joint값을 그대로 
            else:
                # local 
                src_local_mat = src_Tpose_rots[src_j_origin]
                # parent world 
                if src_parent_j_origin is None:
                    src_parent_world_mat = np.eye(3)
                else:
                    src_parent_world_mat = src_world_mats_origin[i, src_parent_j_origin]
                src_world_mat = src_parent_world_mat @ src_local_mat
                src_world_mats_origin[i, src_j_origin] = src_world_mat


    ''' tgt '''
    tgt_world_mats_origin = np.full((len_frame, len(tgt_joints_origin), 3, 3), None, dtype=np.float32)

    # rotation
    for tgt_j_origin, tgt_joint_origin in enumerate(tgt_joints_origin):
        ''' all joint '''
        # parent 
        tgt_parent_name_origin = cmds.listRelatives(tgt_joint_origin, parent=True)[0]

        # root인 경우 (parent joint가 locator)
        # tgt_world_mats: I
        if tgt_parent_name_origin not in tgt_joints_origin:
            tgt_parent_j_origin = None 
            tgt_parent_name_origin = ''
            tgt_world_mats_origin[:, tgt_j_origin] = np.eye(3)
        # 일반 조인트 
        else:
            tgt_parent_j_origin = tgt_joints_origin.index(tgt_parent_name_origin)
            tgt_parent_name_origin = tgt_joints_origin[tgt_parent_j_origin]
        # print("{} {}, parent {} {}".format(tgt_j_origin, tgt_joint_origin, tgt_parent_j_origin, tgt_parent_name_origin))


        ''' common joint'''
        # index 초기화 
        is_common = False
        j, tgt_parent_j, src_joint, tgt_joint = None, None, None, None
        if tgt_joint_origin in tgt_joints:
            is_common = True

            # joint index
            j = tgt_joints.index(tgt_joint_origin)
            src_joint = src_joints[j]
            tgt_joint = tgt_joints[j]
            tgt_parent_j = parent_indices[j]
            tgt_parent_name = tgt_joints[tgt_parent_j]
            # print("     {} {} {}, parent {} {}".format(j, src_joint, tgt_joint, tgt_parent_j, tgt_parent_name))

            # trf
            trf = Tpose_trfs[j]


        ''' update data for frame'''
        tgt_perjoint_local_angle = np.full((len_frame+1, 3), None, dtype=np.float32)
        for i in range(len_frame):
            ''' tgt world '''
            # common joints 
            if is_common:
                # import pdb; pdb.set_trace()
                src_j_origin = src_joints_origin.index(src_joint)
                src_world_mat = src_world_mats_origin[i, src_j_origin]


                """ tgt world """
                # world pure rot. world rot = prerot @ pure rot
                tgt_world_mat = src_world_mat @ trf
                tgt_world_mats_origin[i, tgt_j_origin] = tgt_world_mat

            # not common joint 
            else:
                """ tgt world """
                # local 
                tgt_local_mat = tgt_Tpose_rots[tgt_j_origin]
                # parent world 
                if tgt_parent_j_origin is None:
                    tgt_parent_world_mat = np.eye(3)
                else:
                    tgt_parent_world_mat = tgt_world_mats_origin[i, tgt_parent_j_origin]
                tgt_world_mat = tgt_parent_world_mat @ tgt_local_mat
                tgt_world_mats_origin[i, tgt_j_origin] = tgt_world_mat
                continue # not common joint: end for loop 
            
            
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
                tgt_parent_world_rot = tgt_world_mats_origin[i, tgt_parent_j_origin]

            # local angle
            tgt_local_mat = np.linalg.inv(tgt_parent_world_rot) @ (tgt_world_mat)
            tgt_local_angle = R_to_E(tgt_local_mat)
            tgt_perjoint_local_angle[i] = tgt_local_angle

        # update by joint
        if is_common:
            set_keyframe(tgt_joint, tgt_perjoint_local_angle, rot_attr)
