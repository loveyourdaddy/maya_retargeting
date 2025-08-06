import numpy as np 
import maya.cmds as cmds

# maya rotation order: XYZ
# local rotation multiplication order: ZYX (z축부터 회전시켜야함)

# Rotation matrix
# ZYX 순서로 euler angle 추출
def R_to_E(R, order='zyx'):
    """
    Convert rotation matrix to Euler angles based on specified rotation order.
    
    Args:
        R: 3x3 or 4x4 rotation matrix
        order: rotation order, either 'xyz' or 'zyx' (default: 'xyz')
    
    Returns:
        np.array: [alpha, beta, gamma] in degrees
    """
    # Ensure R is 3x3
    if R.shape == (4, 4):
        R = R[:3, :3]
    
    order = order.lower()
    if order == 'xyz':
        # XYZ order (Maya default)
        beta = np.arcsin(-R[0,2])  # y axis
        
        if np.cos(beta) > 1e-10:  
            # Not at singularity
            alpha = np.arctan2(R[1,2], R[2,2])  # z axis
            gamma = np.arctan2(R[0,1], R[0,0])  # x axis
        else:  
            # At singularity (gimbal lock)
            alpha = 0  # arbitrary
            gamma = np.arctan2(-R[1,0], R[1,1])  # x axis
            
    elif order == 'zyx':
        # ZYX order: local rotation을 구할때 default로 사용
        beta = np.arcsin(-R[2,0])  # y axis
        
        if np.cos(beta) != 0:  
            # Not at singularity
            alpha = np.arctan2(R[2,1], R[2,2])  # z axis
            gamma = np.arctan2(R[1,0], R[0,0])  # x axis
        else:  
            # At singularity (gimbal lock)
            alpha = np.arctan2(-R[1,2], R[1,1])  # z axis
            gamma = 0  # arbitrary
    else:
        raise ValueError(f"Unsupported rotation order: {order}. Use 'xyz' or 'zyx'.")
        
    # Convert to degrees
    alpha = np.degrees(alpha)
    beta = np.degrees(beta)
    gamma = np.degrees(gamma)
    
    return np.array([alpha, beta, gamma])

def R_to_euler(rotmat, order, radians=True):
    """
    Assumes extrinsic rotation and Tait-Bryan angles.
    Alpha, beta, gamma are the angles of rotation about the x, y, z axes respectively.
    TODO: handle gimbal lock (singularities)
    """
    if len(order) != 3:
        raise ValueError(f"Order must be a 3-element list, but got {len(order)} elements")
    
    order = order.lower()
    if set(order) != set("xyz"):
        raise ValueError(f"Invalid order: {order}")
    
    axis2idx = {"x": 0, "y": 1, "z": 2}
    idx0, idx1, idx2 = (axis2idx[axis] for axis in order)

    # compute beta
    sign = -1.0 if (idx0 - idx2) % 3 == 2 else 1.0
    beta = np.arcsin(sign * rotmat[..., idx0, idx2])

    # compute alpha
    sign = -1.0 if (idx0 - idx2) % 3 == 1 else 1.0
    alpha = np.arctan2(sign * rotmat[..., idx1, idx2], rotmat[..., idx2, idx2])

    # compute gamma -> same sign as alpha
    gamma = np.arctan2(sign * rotmat[..., idx0, idx1], rotmat[..., idx0, idx0])

    if not radians:
        alpha, beta, gamma = np.rad2deg(alpha), np.rad2deg(beta), np.rad2deg(gamma)

    return np.stack([alpha, beta, gamma], axis=-1)

# euler
def E_to_R(E, order="xyz", radians=False): # remove order 
    """
    Args:
        E: (..., 3) Euler angles array
        order: str, rotation order (e.g. 'xyz', 'zyx', etc.)
        radians: bool, if True input is in radians, if False in degrees
    Returns:
        R: (..., 3, 3) rotation matrix
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
    
    # Multiply matrices 
    R = [_euler_axis_to_R(E[..., i], order[i]) for i in range(3)]
    # local axis에서는 z, y, x 순서로 곱해야함
    # return np.matmul(np.matmul(R[2], R[1]), R[0])
    return np.matmul(np.matmul(R[0], R[1]), R[2])

def E_to_quat(angles, order, radians=True):
    if not radians:
        angles = np.deg2rad(angles)
    
    def _euler_axis_to_quat(angle, axis):
        zero = np.zeros_like(angle, dtype=np.float32)
        cos  = np.cos(angle / 2, dtype=np.float32)
        sin  = np.sin(angle / 2, dtype=np.float32)

        if axis == "x":
            quat_flat = (cos, sin, zero, zero)
        elif axis == "y":
            quat_flat = (cos, zero, sin, zero)
        elif axis == "z":
            quat_flat = (cos, zero, zero, sin)
        else:
            raise ValueError(f"Invalid axis: {axis}")
        return np.stack(quat_flat, axis=-1).reshape(angle.shape + (4,))
    
    qs = [_euler_axis_to_quat(angles[..., i], order[i]) for i in range(3)]
    return quat_mul(quat_mul(qs[0], qs[1]), qs[2])

# quat 
def quat_to_E(quat, order, radians=True):
    return R_to_euler(quat_to_R(quat), order, radians=radians)

def quat_mul(q0, q1):
    r0, i0, j0, k0 = np.split(q0, 4, axis=-1)
    r1, i1, j1, k1 = np.split(q1, 4, axis=-1)

    res = np.concatenate([
        r0*r1 - i0*i1 - j0*j1 - k0*k1,
        r0*i1 + i0*r1 + j0*k1 - k0*j1,
        r0*j1 - i0*k1 + j0*r1 + k0*i1,
        r0*k1 + i0*j1 - j0*i1 + k0*r1
    ], axis=-1)

    return res

def quat_to_R(quat):
    two_s = 2.0 / np.sum(quat * quat, axis=-1) # (...,)
    r, i, j, k = quat[..., 0], quat[..., 1], quat[..., 2], quat[..., 3]

    rotmat = np.stack([
        1.0 - two_s * (j*j + k*k),
        two_s * (i*j - k*r),
        two_s * (i*k + j*r),
        two_s * (i*j + k*r),
        1.0 - two_s * (i*i + k*k),
        two_s * (j*k - i*r),
        two_s * (i*k - j*r),
        two_s * (j*k + i*r),
        1.0 - two_s * (i*i + j*j)
    ], axis=-1)
    return rotmat.reshape(quat.shape[:-1] + (3, 3)) # (..., 3, 3)

### normalize 
def normalize_rotmat(rot_data):
    # normalize each row of rotation matrix
    for j in range(3):
        rot_data[j] = rot_data[j]/np.linalg.norm(rot_data[j])
    return rot_data

''' rotation in MAYA '''
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


""" additional functions """
def get_rotation_matrix(rot_values, len_frame, inverse=False): 
    if rot_values is None:
        return None
    
    rot_mat = E_to_R(np.array(rot_values))
    if inverse:
        rot_mat = np.linalg.inv(rot_mat)

    return repeat_matrix(rot_mat, len_frame)

def apply_scale(data, scale, inverse=False):
    if scale is not None:
        for i in range(3):
            data[:, i] *= (1/scale[i] if inverse else scale[i])
    return data

def repeat_matrix(matrix, len_frame):
    return matrix[None, :].repeat(len_frame, axis=0)

def apply_rotation(rot_mat, data):
    return np.einsum('ijk,ik->ij', rot_mat, data)