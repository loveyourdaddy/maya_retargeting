import maya.mel as mel
from functions.joints import *
from functions.keyframe import *
from functions.rotations import *

def import_Tpose(char):
    Tpose = "./motions/"+char+"/T-Pose.fbx"
    mel.eval('FBXImport -f"{}"'.format(Tpose))

def get_Tpose_trf(src_joint_hierarchy, tgt_joint_hierarchy):
    # world rotation
    Tpose_trfs = []
    for j, (src_joint, tgt_joint) in enumerate(zip(src_joint_hierarchy, tgt_joint_hierarchy)):
        # get rot matrix 
        # print("src {} tgt {}".format(src_joint, tgt_joint))
        src_rot_data = np.transpose(np.array(cmds.xform(src_joint, q=True, ws=True, matrix=True)).reshape(4,4)[:3,:3])
        tgt_rot_data = np.transpose(np.array(cmds.xform(tgt_joint, q=True, ws=True, matrix=True)).reshape(4,4)[:3,:3])

        # normalize rotation matrix
        src_rot_data = normalize_rotmat(src_rot_data)
        tgt_rot_data = normalize_rotmat(tgt_rot_data)

        # trf 
        trf = np.linalg.inv(src_rot_data) @ tgt_rot_data
        Tpose_trfs.append(trf)
    
    return Tpose_trfs

def retarget_translation(src_hip, tgt_hip, 
                         src_locator=None, src_locator_rot=None, src_locator_scale=None,
                         tgt_locator=None, tgt_locator_rot=None, tgt_locator_scale=None, 
                         translate=None):
    # translation
    trans_data, _ = get_keyframe_data(src_hip) 
    trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
    trans_data = get_array_from_keyframe_data(trans_data, trans_attr)
    len_frame = len(trans_data)
    # if translate is not None:
    #     translate = translate[None, :].repeat(len_frame, axis=0)

    # update position
    if len_frame!=0:
        # no locator
        if src_locator==None and tgt_locator==None:
            print(">> no locator")
            if translate is not None:
                trans_data[:, ] += translate

            set_keyframe(tgt_hip, trans_data, trans_attr)

        # src
        elif src_locator!=None and tgt_locator==None:
            print(">> src locator {} ".format(src_locator))
            src_locator_rot_mat = E_to_R(np.array(src_locator_rot))
            src_locator_rot_mat = src_locator_rot_mat[None, :].repeat(len_frame, axis=0)
            tgt_trans_data = np.einsum('ijk,ik->ij', src_locator_rot_mat, trans_data)
            
            # scale translation
            for i in range(3): # x, y, z
                tgt_trans_data[:, i] *= src_locator_scale[i]

            # update position
            if translate is not None:
                tgt_trans_data[:, ] += np.einsum('ijk,ik->ij', src_locator_rot_mat, translate)
            set_keyframe(tgt_hip, tgt_trans_data, trans_attr)

        # tgt
        elif src_locator==None and tgt_locator!=None:
            print(">> tgt locator {} ".format(tgt_locator))
            tgt_locator_rot_mat = E_to_R(-1 * np.array(tgt_locator_rot))
            tgt_locator_rot_mat = tgt_locator_rot_mat[None, :].repeat(len_frame, axis=0)
            tgt_trans_data = np.einsum('ijk,ik->ij', tgt_locator_rot_mat, trans_data)
            
            # scale translation
            for i in range(3): # x, y, z
                tgt_trans_data[:, i] /= tgt_locator_scale[i]

            # update position
            if translate is not None:
                tgt_trans_data[:, ] += np.einsum('ijk,ik->ij', src_locator_rot_mat, translate) 
            set_keyframe(tgt_hip, tgt_trans_data, trans_attr)

        # both src and tgt
        elif src_locator!=None and tgt_locator!=None:
            print(">> src locator {} tgt locator {}".format(src_locator, tgt_locator))
            # print("before \n", trans_data[0])

            src_locator_rot_mat = E_to_R(np.array(src_locator_rot))
            src_locator_rot_mat = src_locator_rot_mat[None, :].repeat(len_frame, axis=0)

            # tgt_locator_rot_mat = E_to_R(-1 * np.array(tgt_locator_rot))
            # print("tgt_locator_rot_mat before \n", E_to_R(-1 * np.array(tgt_locator_rot)))
            tgt_locator_rot_mat = np.linalg.inv(E_to_R(np.array(tgt_locator_rot)))
            # print("tgt_locator_rot_mat after  \n", tgt_locator_rot_mat)
            tgt_locator_rot_mat = tgt_locator_rot_mat[None, :].repeat(len_frame, axis=0)

            tgt_trans_data = np.einsum('ijk,ik->ij', src_locator_rot_mat, trans_data)
            # print("after1 \n", tgt_trans_data[0])
            tgt_trans_data = np.einsum('ijk,ik->ij', tgt_locator_rot_mat, tgt_trans_data)
            # print("after2 \n", tgt_trans_data[0])

            # if translate is not None:
            #     print("{} {} {}".format(tgt_locator_rot_mat.shape, src_locator_rot_mat.shape, translate.shape))
            #     tgt_trans_data[:, ] += np.matmul(tgt_locator_rot_mat, np.matmul(src_locator_rot_mat, translate))

            # scale translation
            for i in range(3): # x, y, z
                tgt_trans_data[:, i] *= src_locator_scale[i]
                tgt_trans_data[:, i] /= tgt_locator_scale[i]

            # update position
            # TODO: 기존 값을 받아와서 업데이트하기
            # if translate is not None:
            #     for attr_idx, attr in enumerate(trans_attr.keys()):
            #         for tid, _ in enumerate(tgt_trans_data):
            #             # print(translate[attr_idx])
            #             cmds.setKeyframe(tgt_locator, attribute=attr, time=tid, value=float(translate[attr_idx]))
            set_keyframe(tgt_hip, tgt_trans_data, trans_attr)
        
        else:
            raise ValueError("locator error")

    return trans_data

def retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, \
                      len_frame, src_locator_rot=None, tgt_locator_rot=None,\
                        prerotations=None):
    # rotation
    # assumtion: src and tgt have same joint names
    src_world_mats = np.full((len_frame, len(tgt_joints), 3, 3), None, dtype=np.float32)
    tgt_world_mats = np.full((len_frame, len(tgt_joints), 3, 3), None, dtype=np.float32)
    for j, (src_joint, tgt_joint) in enumerate(zip(src_joints, tgt_joints)):
        parent_j = parent_indices[j]
        print("{} {} {} parent{}".format(j, src_joint, tgt_joint, parent_j))

        # keyframe_data
        # [attr, frames, (frame, value)]: (trans, world rot)
        _, rot_data = get_keyframe_data(src_joint)

        # tgt angle from src
        rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
        rot_data = get_array_from_keyframe_data(rot_data, rot_attr)
        if rot_data.shape[0]!=len_frame:
            print("rot_data {} of joint {} is not matched with len_frame{}".format(
                rot_data.shape, src_joint, len_frame))
            continue
        src_to_tgt_trf = Tpose_trfs[j]

        # prerot
        prerot = prerotations[j]

        # parent prerot
        if j==0:
            # because parent is None
            parent_prerot = np.eye(3)
        else:
            parent_prerot = prerotations[parent_j]

        # update data
        tgt_perjoint_local_angle = np.full((len_frame+1, 3), None, dtype=np.float32)
        for i in range(len_frame):
            """ src """
            # local angle
            src_local_angle = rot_data[i]
            src_local_mat = E_to_R(src_local_angle)

            # parent angle
            if j==0:
                if src_locator_rot is not None:
                    # if i==0:
                        # print("src locator")
                    src_parent_rot_mat = E_to_R(np.array(src_locator_rot))
                else:
                    # if i==0:
                        # print("no src locator")
                    src_parent_rot_mat = E_to_R(np.array([0,0,0]))
            else:
                # tgt parent world rot
                src_parent_rot_mat = src_world_mats[i, parent_j]

            # world angle
            src_world_mat = src_parent_rot_mat @ src_local_mat
            src_world_mats[i, j] = src_world_mat

            """ tgt """
            # world angle 
            tgt_world_mat = src_world_mat @ src_to_tgt_trf
            tgt_world_mats[i, j] = tgt_world_mat

            # parent world rot
            if j==0:
                # locator
                if tgt_locator_rot is not None:
                    tgt_parent_rotmat = E_to_R(np.array(tgt_locator_rot))
                # src locator, no tgt locator
                else:
                    tgt_parent_rotmat = E_to_R(np.array([0,0,0]))
            else:
                # tgt parent world rot
                tgt_parent_rotmat = tgt_world_mats[i, parent_j]

            # update by frame
            # prerot * inv(parent_rot) * world_rot
            parent_rot = np.linalg.inv(parent_prerot) @ tgt_parent_rotmat # parent world rotation without prerot
            tgt_local_mat = np.linalg.inv(parent_rot) @ np.linalg.inv(prerot) @ tgt_world_mat
            # tgt_local_mat = np.linalg.inv(tgt_parent_rotmat) @ np.linalg.inv(prerot) @ tgt_world_mat

            tgt_local_angle = R_to_E(tgt_local_mat)
            tgt_perjoint_local_angle[i] = tgt_local_angle

        # update by joint
        set_keyframe(tgt_joint, tgt_perjoint_local_angle, rot_attr)
