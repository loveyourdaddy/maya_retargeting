import numpy as np 
import maya.cmds as cmds

# xyz euler angles
def R_to_E(R):
    beta = np.arcsin(-R[2, 0]) # beta (y axis)
    # print("{} {}".format(-R[2, 0], beta))
    
    # Calculate alpha(z axis) and gamma (x axis) based on the value of cos(beta)
    if np.cos(beta) != 0:
        alpha = np.arctan2(R[2, 1], R[2, 2])
        gamma = np.arctan2(R[1, 0], R[0, 0])
    else:
        alpha = np.arctan2(-R[1, 2], R[1, 1])
        gamma = 0

    # Convert radians to degrees
    alpha = np.degrees(alpha)
    beta = np.degrees(beta)
    gamma = np.degrees(gamma)

    return np.array([alpha, beta, gamma])

# For ZYX Euler angles
def R_to_E_(R):
    beta = np.arcsin(-R[0,2])  # beta (y axis)
    
    if np.cos(beta) > 1e-10:  # Not at singularity
        alpha = np.arctan2(R[1,2], R[2,2])  # z axis
        gamma = np.arctan2(R[0,1], R[0,0])  # x axis
    else:  # At singularity
        alpha = 0  # arbitrary
        gamma = np.arctan2(-R[1,0], R[1,1])
        
    # Convert to degrees
    alpha = np.degrees(alpha)
    beta = np.degrees(beta)
    gamma = np.degrees(gamma)
    
    return np.array([alpha, beta, gamma])

def E_to_R(E, order="xyz", radians=False): # order: rotation값이 들어오는 순서
    """
    Args:
        E: (..., 3)
    """
    if E.shape[-1] != 3:
        raise ValueError(f"Invalid Euler angles shape {E.shape}")
    if len(order) != 3:
        raise ValueError(f"Order must have 3 characters, but got {order}")

    if not radians:
        E = np.deg2rad(E)

    def _euler_axis_to_R(angle, axis):
        one  = np.ones_like(angle, dtype=np.float32)
        zero = np.zeros_like(angle, dtype=np.float32)
        cos  = np.cos(angle, dtype=np.float32)
        sin  = np.sin(angle, dtype=np.float32)

        if axis == "x":
            R_flat = (one, zero, zero, zero, cos, -sin, zero, sin, cos)
        elif axis == "y":
            R_flat = (cos, zero, sin, zero, one, zero, -sin, zero, cos)
        elif axis == "z":
            R_flat = (cos, -sin, zero, sin, cos, zero, zero, zero, one)
        else:
            raise ValueError(f"Invalid axis: {axis}")
        return np.stack(R_flat, axis=-1).reshape(angle.shape + (3, 3))
    R = [_euler_axis_to_R(E[..., i], order[i]) for i in range(3)]

    # rotation multiplication order: ZYX (Rz * Ry * Rx)
    R = np.matmul(np.matmul(R[2], R[1]), R[0])
    
    return R

def normalize_rotmat(rot_data):
    # normalize each row of rotation matrix
    for j in range(3):
        rot_data[j] = rot_data[j]/np.linalg.norm(rot_data[j])
    return rot_data


''' rotation in MAYA '''
# get src delta rotation (assumption: first frame is Tpose)
def get_rot_mat(src_joint, bool_worldSpace):
    tgt_Tpose_rot = cmds.xform(src_joint, query=True, worldSpace=bool_worldSpace, rotation=True)
    tgt_Tpose_rot = np.array(tgt_Tpose_rot)
    tgt_Tpose_rot = E_to_R(tgt_Tpose_rot)
    return tgt_Tpose_rot

def get_world_rot_data(joint_name):
    # Get rotation keyframe data
    rot_data = cmds.keyframe(joint_name, query=True, attribute='rotate', valueChange=True, timeChange=True)
    
    # Organize the data into arrays
    rot_data_array = np.array(rot_data).reshape(-1, 2) # 6038 -> [3*3018, 2] 
    max_time = int(np.max(rot_data_array[:, 0]))
    min_time = 0
    
    rot_data = np.full((max_time+1-min_time, 3), None, dtype=np.float32)
    attr_idx = 0
    prev_time = -1
    for data in rot_data_array:
        time = int(data[0])
        rot = data[1]
        if prev_time > time:
            attr_idx += 1
        rot_data[time, attr_idx] = rot 
        prev_time = time

    # interpolation
    len_frame = len(rot_data)
    for attr_idx in range(3):
        # if first first is nan
        if np.isnan(rot_data[0][attr_idx]):
            for f in range(len_frame):
                if np.isnan(rot_data[f][attr_idx])==False:
                    rot_data[0][attr_idx] = rot_data[f][attr_idx]
                    break

        # interpolation 
        for fid in range(len_frame):
            condition = np.isnan(rot_data[fid][attr_idx])
            if condition:
                rot_data[fid][attr_idx] = rot_data[fid-1][attr_idx]

    return rot_data
