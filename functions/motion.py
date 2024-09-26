import maya.mel as mel
from functions.joints import *
from functions.keyframe import *
from functions.rotations import *

def import_Tpose(char):
    Tpose = "./motions/"+char+"/T-Pose.fbx"
    mel.eval('FBXImport -f"{}"'.format(Tpose))

""" Trf between characters """
def get_Tpose_trf(src_joint_hierarchy, tgt_joint_hierarchy, tgt_prerotations=None):
    # trf: src와 tgt간의 pure rotation 관계

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

        # prerot
        # world rot = prerot @ pure rot
        # tgt_rot_data = np.linalg.inv(tgt_prerotations[j]) @ tgt_rot_data
        # tgt_rot_data = tgt_rot_data @ np.linalg.inv(tgt_prerotations[j])
        # tgt_rot_data = tgt_rot_data @ tgt_prerotations[j]

        # trf
        # tgt_world_mat = trf @ src_world_mat
        trf = np.linalg.inv(src_rot_data) @ tgt_rot_data
        # trf = tgt_rot_data @ np.linalg.inv(src_rot_data)
        Tpose_trfs.append(trf)
    
    return Tpose_trfs

def retarget_translation(src_hip, tgt_hip, 
                         src_locator=None, src_locator_rot=None, src_locator_scale=None,
                         tgt_locator=None, tgt_locator_rot=None, tgt_locator_scale=None, 
                         height_ratio=1):
    # translation
    trans_data, _ = get_keyframe_data(src_hip) 
    trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
    trans_data = get_array_from_keyframe_data(trans_data, trans_attr)
    len_frame = len(trans_data)

    # update position
    if len_frame!=0:
        # no locator
        if src_locator==None and tgt_locator==None:
            print(">> no locator")

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
            # print("tgt_locator_rot_mat before \n", E_to_R(-1 * np.array(tgt_locator_rot)))
            tgt_locator_rot_mat = np.linalg.inv(E_to_R(np.array(tgt_locator_rot)))
            # print("tgt_locator_rot_mat after  \n", tgt_locator_rot_mat)
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

def retarget_rotation(src_joints, tgt_joints, Tpose_trfs, parent_indices, \
                      len_frame, src_locator_rot=None, tgt_locator_rot=None,\
                        tgt_prerotations=None):
    # tgt_prerotations=None

    # rotation
    src_world_mats = np.full((len_frame, len(tgt_joints), 3, 3), None, dtype=np.float32)
    tgt_world_mats = np.full((len_frame, len(tgt_joints), 3, 3), None, dtype=np.float32)
    for j, (src_joint, tgt_joint) in enumerate(zip(src_joints, tgt_joints)):
        parent_j = parent_indices[j]
        # print("{} {} {} parent{}".format(j, src_joint, tgt_joint, parent_j))

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

        # trf 
        trf = Tpose_trfs[j]

        # tgt prerot
        if tgt_prerotations is not None:
            prerot = tgt_prerotations[j]

            # parent prerot
            if j==0:
                # because parent is None
                parent_prerot = np.eye(3) # prerot
            else:
                parent_prerot = tgt_prerotations[parent_j]

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
                    src_parent_rot_mat = E_to_R(np.array(src_locator_rot))
                else:
                    src_parent_rot_mat = E_to_R(np.array([0,0,0]))
            else:
                # tgt parent world rot
                src_parent_rot_mat = src_world_mats[i, parent_j]

            # world angle
            src_world_mat = src_parent_rot_mat @ src_local_mat
            src_world_mats[i, j] = src_world_mat

            """ tgt """
            # world pure rot. world rot = prerot @ pure rot
            tgt_world_mat = src_world_mat @ trf
            tgt_world_mats[i, j] = tgt_world_mat

            # parent world rot
            if j==0:
                # locator
                if tgt_locator_rot is not None:
                    tgt_parent_world_rot = E_to_R(np.array(tgt_locator_rot))
                # src locator, no tgt locator
                else:
                    tgt_parent_world_rot = E_to_R(np.array([0,0,0])) # tgt_world_mat # 
            else:
                # tgt parent world rot
                tgt_parent_world_rot = tgt_world_mats[i, parent_j]

            # local angle
            # TODO: prerotation
            # tgt_local_mat = np.linalg.inv(np.linalg.inv(parent_prerot) @ tgt_parent_world_rot) @ (np.linalg.inv(prerot) @ tgt_world_mat)
            tgt_local_mat = np.linalg.inv(tgt_parent_world_rot) @ (tgt_world_mat)
            tgt_local_angle = R_to_E(tgt_local_mat)
            tgt_perjoint_local_angle[i] = tgt_local_angle
        # update by joint
        set_keyframe(tgt_joint, tgt_perjoint_local_angle, rot_attr)
