import maya.cmds as cmds
from functions.joints import *
from functions.keyframe import *
from functions.rotations import *
from functions.motion import *
import math
import maya.api.OpenMaya as om

def get_conversion(src_joints_origin, src_joints_template,
                    tgt_joints_origin, tgt_joints_template, tgt_joints_template_indices, 
                    root_joint=None):
    # common hierarchy
    src_indices, tgt_indices = get_common_hierarchy_bw_src_and_tgt(
        src_joints_origin, src_joints_template, # src 
        tgt_joints_origin, tgt_joints_template, root_joint, # tgt 
        )
    
    # indices 
    # refined joint에서 인덱스을 얻을 후, tgt joints에서 뽑기
    src_joints_common = [src_joints_origin[i] for i in src_indices]
    tgt_joints_common = [tgt_joints_origin[i] for i in tgt_indices]

    # indices 
    tgt_joints_template_indices = [tgt_joints_template_indices[i] for i in tgt_indices]

    # Tpose rot common
    tgt_Tpose_rots_common = get_Tpose_localrot(tgt_joints_common)
    src_Tpose_rots_common = get_Tpose_localrot(src_joints_common)

    # Tpose trf
    conversion_matrics = get_conversion_matrix(src_joints_common, tgt_joints_common)

    return src_joints_common, src_Tpose_rots_common, \
        tgt_joints_common, tgt_Tpose_rots_common, tgt_joints_template_indices, \
        conversion_matrics

''' common joint hierarchy '''
def get_common_hierarchy_bw_src_and_tgt(
        src_joints_origin, src_joints_template, 
        tgt_joints_origin, tgt_joints_template, root_joint=None):
    # jid, name
    tgt_root_div_jid, tgt_root_div, tgt_spine_div_jid, tgt_spine_div = get_division_by_name(tgt_joints_origin, tgt_joints_template, root_joint=root_joint)
    src_root_div_jid, src_root_div, src_spine_div_jid, src_spine_div = get_division_by_name(src_joints_origin, src_joints_template)

    # 만약 root joint을 찾을 수 없다면, 분기점으로 name을 바꿔주기
    if tgt_root_div_jid==-1:
        def find_skeleton_by_hierarchy(joints_wo_name):
            # 가정: root -> spine (-> left arm -> right arm) -> left leg -> right leg 
            root_div_jid = -1
            spine_div_jid = -1
            ee_joints = []
            for jid, tgt_joint in enumerate(joints_wo_name):
                children = cmds.listRelatives(tgt_joint, children=True)
                if children is not None:
                    children = [child for child in children if children and cmds.nodeType(child) == 'joint']
                    if len(children)==0:
                        children = None
                # print("tgt joint {} children {}".format(tgt_joint, children))

                # root 
                if children is not None and len(children)>1 and root_div_jid==-1 and spine_div_jid==-1:
                    name = "tgt:Hips"
                    cmds.rename(tgt_joint, name)
                    joints_wo_name[jid] = name
                    root_div_jid = jid
                    root_div = name
                    # print("tgt root div")
                    continue

                # spine
                if children is not None and len(children)>1 and root_div_jid!=-1 and spine_div_jid==-1:
                    name = "tgt:Spine"
                    cmds.rename(tgt_joint, name)
                    joints_wo_name[jid] = name
                    spine_div_jid = jid
                    spine_div = name
                    # print("tgt spine div")
                    continue
                
                if children is None: # and len(children)==0 
                    if len(ee_joints)==0:
                        name = "tgt:LeftHand"
                        joints_wo_name[jid] = name
                    elif len(ee_joints)==1:
                        name = "tgt:RightHand"
                        joints_wo_name[jid] = name
                    elif len(ee_joints)==2:
                        name = "tgt:Head"
                        joints_wo_name[jid] = name
                    elif len(ee_joints)==3:
                        name = "tgt:LeftToeBase"
                        joints_wo_name[jid] = name
                    elif len(ee_joints)==4:
                        name = "tgt:RightToeBase"
                        joints_wo_name[jid] = name
                    else:
                        raise("ee joints are more than 5")
                    ee_joints.append(jid)
                    cmds.rename(tgt_joint, name)
            
            # 분기점 사이의 조인트의 이름을 바꿔주기
            spine_idx = 0
            for jid, tgt_joint in enumerate(joints_wo_name):
                name = None 

                # spine 
                if jid > root_div_jid and jid < spine_div_jid:
                    spine_idx += 1
                    name = "tgt:Spine" + str(spine_idx)
                    joints_wo_name[jid] = name
                # left arm
                if jid > spine_div_jid and jid < ee_joints[0]:
                    if jid == spine_div_jid+1:
                        name = "tgt:LeftShoulder"
                    elif jid == spine_div_jid+2:
                        name = "tgt:LeftArm"
                    elif jid == spine_div_jid+3:
                        name = "tgt:LeftForeArm"
                    joints_wo_name[jid] = name
                # right arm
                if jid > ee_joints[0] and jid < ee_joints[1]:
                    if jid == spine_div_jid+1:
                        name = "tgt:RightShoulder"
                    elif jid == spine_div_jid+2:
                        name  = "tgt:RightArm"
                    elif jid == spine_div_jid+3:
                        name = "tgt:RightForeArm"
                    joints_wo_name[jid] = name 
                # neck
                if jid > ee_joints[1] and jid < ee_joints[2]:
                    if jid == spine_div_jid+1:
                        name = "tgt:Neck"
                        joints_wo_name[jid] =name 
                # left leg
                if jid > ee_joints[2] and jid < ee_joints[3]:
                    if jid == ee_joints[2]+1:
                        name = "tgt:LeftUpLeg"
                    elif jid == ee_joints[2]+2:
                        name=  "tgt:LeftLeg"
                    elif jid == ee_joints[2]+3:
                        name = "tgt:LeftFoot"
                    joints_wo_name[jid] = name 
                # right leg
                if jid > ee_joints[3] and jid < ee_joints[4]:
                    if jid == ee_joints[3]+1:
                        name = "tgt:RightUpLeg"
                    elif jid == ee_joints[3]+2:
                        name = "tgt:RightLeg"
                    elif jid == ee_joints[3]+3:
                        name = "tgt:RightFoot"
                    joints_wo_name[jid] = name 
                # rename 
                if name is not None:
                    cmds.rename(tgt_joint, name)

            return joints_wo_name, root_div_jid, root_div, spine_div_jid, spine_div
        
        tgt_joints_template, tgt_root_div_jid, tgt_root_div, tgt_spine_div_jid, tgt_spine_div = find_skeleton_by_hierarchy(tgt_joints_origin)

    # remove namespace
    src_root_div = src_root_div.split(':')[-1]
    tgt_root_div = tgt_root_div.split(':')[-1]
    src_spine_div = src_spine_div.split(':')[-1]
    tgt_spine_div = tgt_spine_div.split(':')[-1]

    # get common joints 
    ''' 
    Divison 예외처리: 
    - 만약 joint가 spine div조인트를 넘어갔고, 리스트에 없다면 
    - 마지막 조인트를 1개 빼주고(spine이 1개 이상있다고 가정.) division joint을 넣어주기
    '''
    src_common_joint = []
    tgt_common_joint = []
    src_indices = []
    tgt_indices = []
    root_check_flag = False
    spine_check_flag = False
    for src_idx, src_joint in enumerate(src_joints_template):
        # Hips 이름 중복에 대한 예외처리
        # 이름이 같고, src_root_div_jid보다 작다면, continue
        if src_joint.lower() == src_root_div.lower() and src_idx < src_root_div_jid:
            continue

        check = False
        for tgt_idx, tgt_joint in enumerate(tgt_joints_template):
            src_joint_renamed = src_joint.split(':')[-1]
            tgt_joint_renamed = tgt_joint.split(':')[-1]

            # find common joint
            if (src_joint_renamed.lower() in tgt_joint_renamed.lower() or tgt_joint_renamed.lower() in src_joint_renamed.lower()) \
                    and (src_joint not in src_common_joint and tgt_joint not in tgt_common_joint):
                # print("src {} tgt {}".format(src_joint, tgt_joint))

                # add root division
                # division의 다음 조인트로 넘어갔을때, 이전 조인트를 강제로 division 조인트로 바꿔주기
                if root_check_flag==False and src_idx > src_root_div_jid and tgt_idx > tgt_root_div_jid:
                    if src_joint not in src_common_joint and tgt_joint not in tgt_common_joint:
                        if len(src_common_joint)==0:
                            src_common_joint.append(src_root_div)
                            src_indices.append(src_root_div_jid)
                            tgt_common_joint.append(tgt_root_div)
                            tgt_indices.append(tgt_root_div_jid)
                        else:
                            src_common_joint[-1] = src_root_div
                            src_indices[-1] = src_root_div_jid
                            tgt_common_joint[-1] = tgt_root_div
                            tgt_indices[-1] = tgt_root_div_jid

                    root_check_flag = True
                    # break

                # add spine division
                if spine_check_flag==False and src_idx > src_spine_div_jid and tgt_idx > tgt_spine_div_jid:
                    if src_joint not in src_common_joint and tgt_joint not in tgt_common_joint:
                        if src_indices[-1]!=src_root_div_jid and tgt_indices[-1]!=tgt_root_div_jid:
                            # 이미 들어와있는 조인트의 마지막이 hips가 아니라면, spine division을 넣어주기
                            src_common_joint[-1] = src_spine_div
                            src_indices[-1] = src_spine_div_jid
                            tgt_common_joint[-1] = tgt_spine_div
                            tgt_indices[-1] = tgt_spine_div_jid
                        else:
                            # hips라면, 새로 추가
                            src_common_joint.append(src_spine_div)
                            src_indices.append(src_spine_div_jid)
                            tgt_common_joint.append(tgt_spine_div)
                            tgt_indices.append(tgt_spine_div_jid)
                    
                    spine_check_flag = True
                    # break

                src_common_joint.append(src_joint)
                tgt_common_joint.append(tgt_joint)
                src_indices.append(src_idx)
                tgt_indices.append(tgt_idx)
                check = True
                # print("src {} {} tgt {} {}".format(src_idx, src_joint, tgt_idx, tgt_joint))
                break
        if check:
            continue
     
    return src_indices, tgt_indices

def check_joint_by_template_names(joint_name, template_names):
    for template_name in template_names:
        if joint_name.lower() in template_name.lower() or template_name.lower() in joint_name.lower():
            return True
    return False

def get_division_by_name(joint_hierarchy_origin, joint_hierarchy_template, root_joint=None):
    ''' 
    division 조건
    - children이 1개 초과
    '''
    # division
    root_names = alter_joint_name["Hips"] + ["Hips"]
    spine_names = alter_joint_name["Spine"] + ["spine", "chest"]

    root_joints, spine_joints = [], []
    for i, joint_name in enumerate(joint_hierarchy_origin):
        children = cmds.listRelatives(joint_name, children=True, type='joint')

        # 예외처리: 조인트가 ee 
        if children is None:
            continue

        # 만약 child의 child가 없다면, children에서 제외해주기. 
        filtered_children = []
        for child in children:
            if cmds.listRelatives(child, children=True, type='joint') is not None:
                filtered_children.append(child)
        children = filtered_children

        if joint_name in joint_hierarchy_origin:
            jid = joint_hierarchy_origin.index(joint_name)
            joint_name_template = joint_hierarchy_template[jid]
        # print("joint {} joint_name_template {}".format(joint_name, joint_name_template))

        # division0: root 
        if children is not None and len(children)>1 and check_joint_by_template_names(joint_name_template, root_names):
            root_joints.append(joint_name_template)
            continue

        # division1: spine 
        if children is not None and len(children)>1 and check_joint_by_template_names(joint_name_template, spine_names):
            spine_joints.append(joint_name_template)
            continue

    # 만약 root joint을 찾을 수 없다면, 이름으로 찾지 않고 skeletal chain으로 찾기
    if len(root_joints)==0:
        return -1, "", -1, ""

    # 가장 마지막을 division으로 설정
    # Spine 
    spine_name = spine_joints[-1]
    spine_jid = joint_hierarchy_template.index(spine_name)

    # Root: 마지막 root 및 spine joint 보다 인덱스가 작은것
    if root_joint is None:
        root_joints = [joint for joint in root_joints if joint_hierarchy_template.index(joint) < spine_jid]
        root_name = root_joints[-1]
        root_jid = len(joint_hierarchy_template) - 1 - joint_hierarchy_template[::-1].index(root_name) # 리스트를 뒤집고 첫 번째 'Hips'의 인덱스를 찾은 후, 원래 리스트로 뒤집기
    else:
        # if root joint is given
        root_jid = joint_hierarchy_template.index(root_joint)
        root_name = root_joint

    return root_jid, root_name, spine_jid, spine_name

def get_common_substring(str1_, str2_):
    str1 = str1_.lower() 
    str2 = str2_.lower() 

    m = len(str1)
    n = len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    max_length = 0
    end_position = 0
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
                if dp[i][j] > max_length:
                    max_length = dp[i][j]
                    end_position = i
                    
    return str1[end_position - max_length:end_position]

def check_string_in_list(string, string_list):
    string_list_lower = [value.lower() for value in string_list]
    string_lower = string.lower()
    # string이 list에 정확히 겹치는 것이 있거나, list의 각 인자가 string에 포함되는 경우
    if string_lower in string_list_lower or any(val in string_lower for val in string_list_lower):
        return True
    else:
        return False

""" Tpose """
def get_Tpose_trf(src_joint_hierarchy, tgt_joint_hierarchy, tgt_prerotations=None):
    # world rotation
    Tpose_trfs = []
    for j, (src_joint, tgt_joint) in enumerate(zip(src_joint_hierarchy, tgt_joint_hierarchy)):
        # get rot matrix 
        # print("src {} tgt {}".format(src_joint, tgt_joint))
        src_rot_data = get_worldrot_of_joint(src_joint)
        tgt_rot_data = get_worldrot_of_joint(tgt_joint)

        trf = np.linalg.inv(src_rot_data) @ tgt_rot_data
        # trf = tgt_rot_data @ np.linalg.inv(src_rot_data)
        Tpose_trfs.append(trf)
    
    return Tpose_trfs

""" motion """
def get_conversion_matrix(src_joint_hierarchy, tgt_joint_hierarchy):
    # x, y, z vector in world space
    def get_axis_vec_in_world_space(joint_name):
        import maya.OpenMaya as om
        matrix = cmds.xform(joint_name, query=True, worldSpace=True, matrix=True)
        m_matrix = om.MMatrix()
        om.MScriptUtil.createMatrixFromList(matrix, m_matrix)
        transform = om.MTransformationMatrix(m_matrix)
        m_matrix = transform.asMatrix()

        # 각 축의 벡터 추출
        x_axis = np.array([m_matrix(0, 0), m_matrix(0, 1), m_matrix(0, 2)])
        y_axis = np.array([m_matrix(1, 0), m_matrix(1, 1), m_matrix(1, 2)])
        z_axis = np.array([m_matrix(2, 0), m_matrix(2, 1), m_matrix(2, 2)])
        # normalize each 
        x_axis = x_axis / np.linalg.norm(x_axis)
        y_axis = y_axis / np.linalg.norm(y_axis)
        z_axis = z_axis / np.linalg.norm(z_axis)

        # matrix 
        orientation = np.array([x_axis, y_axis, z_axis])

        return orientation
    
    t_matricies = []
    len_joint = len(src_joint_hierarchy)
    for j in range(len_joint):
        src_ori = get_axis_vec_in_world_space(src_joint_hierarchy[j])
        tgt_ori = get_axis_vec_in_world_space(tgt_joint_hierarchy[j])
        
        # conversion matrix 
        t_mat = tgt_ori @ np.linalg.inv(src_ori) 
        t_matricies.append(t_mat)

    return t_matricies

def retarget_translation(src_hip, tgt_hip, 
                         subchain_roots, 
                         src_locator=None, src_locator_rot=None, src_locator_scale=None,
                         tgt_locator=None, tgt_locator_rot=None, tgt_locator_scale=None, tgt_locator_pos=None, 
                         height_ratio=1, hip_height_diff=[]):
    # translation data
    trans_data, _ = get_keyframe_data(src_hip)
    trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
    trans_data = get_array_from_keyframe_data(trans_data, trans_attr, src_hip)
    len_frame = len(trans_data)

    if len_frame == 0:
        return trans_data
    
    """ 위치 데이터를 locator 기반으로 변환하는 함수 """
    def apply_rotation(rot_mat, data):
        return np.einsum('ijk,ik->ij', rot_mat, data)
    
    def repeat_matrix(matrix):
        return matrix[None, :].repeat(len_frame, axis=0)
    
    def get_rotation_matrix(rot_values, inverse=False):
        if rot_values is None:
            return None
        rot_mat = E_to_R(np.array(rot_values))
        if inverse:
            rot_mat = np.linalg.inv(rot_mat)
        return repeat_matrix(rot_mat)
    
    def apply_scale(data, scale, inverse=False):
        if scale is not None:
            for i in range(3):
                data[:, i] *= (1/scale[i] if inverse else scale[i])
        return data

    # Source locator 처리
    if src_locator:
        src_rot_mat = get_rotation_matrix(src_locator_rot)
        trans_data = apply_rotation(src_rot_mat, trans_data)
        trans_data = apply_scale(trans_data, src_locator_scale)

    # Target locator 처리
    if tgt_locator:
        tgt_rot_mat = get_rotation_matrix(tgt_locator_rot, inverse=True)
        trans_data = apply_rotation(tgt_rot_mat, trans_data)
        
        # locator 포지션 반영
        if tgt_locator_pos is not None:
            tgt_pos = repeat_matrix(np.array(tgt_locator_pos))
            if src_locator:
                tgt_pos = apply_rotation(src_rot_mat, tgt_pos)
            tgt_pos = apply_rotation(tgt_rot_mat, tgt_pos)
            trans_data = trans_data - tgt_pos
        
        trans_data = apply_scale(trans_data, tgt_locator_scale, inverse=True)

        trans_data_main = trans_data * height_ratio
        # trans_data_main = trans_data * height_ratio
        set_keyframe(tgt_hip, trans_data_main, trans_attr)

        # subchain
        for i, subchain_root in enumerate(subchain_roots):
            diff = hip_height_diff[i]
            # trans_data_sub = trans_data_main - (trans_data * diff)
            # y값: 차이를 main root의 delta 값으로 사용
            trans_data_sub = trans_data_main - (trans_data_main * (height_ratio - diff))

            # x, z 값은 같게
            # y_axis = (tgt_rot_mat[0] @ np.array([0,1,0])) 
            x_axis = (tgt_rot_mat[0] @ np.array([1,0,0])) 
            z_axis = (tgt_rot_mat[0] @ np.array([0,0,1])) 
            x_component = int(np.argmax(np.abs(x_axis)))
            z_component = int(np.argmax(np.abs(z_axis)))

            trans_data_sub[:, x_component] = trans_data_main[:, x_component]
            trans_data_sub[:, z_component] = trans_data_main[:, z_component]
            # import pdb; pdb.set_trace()
            
            # import pdb; pdb.set_trace()
            # trans_data_sub_ = trans_data * diff
            set_keyframe(subchain_root, trans_data_sub, trans_attr)

    return trans_data

def matrix_to_mmatrix(matrix):
    # For 3x3 rotation matrix
    if matrix.shape == (3, 3):
        # Convert 3x3 to 4x4 by adding translation and perspective components
        matrix_4x4 = np.eye(4)
        matrix_4x4[:3, :3] = matrix
    else:
        matrix_4x4 = matrix
    
    # Flatten the matrix and convert to list for MMatrix constructor
    matrix_list = matrix_4x4.flatten().tolist()
    
    # Create MMatrix directly from the flattened list
    return om.MMatrix(matrix_list)

def retarget_rotation(src_common_joints, src_Tpose_localrots, # src {}
                      tgt_common_joints, tgt_Tpose_localrots, tgt_joints_template_indices,  Tpose_trfs, # tgt
                      tgt_subchains, subchain_Tpose_localrots, tgt_subchain_template_indices, subchain_Tpose_trfs, # subchaint
                      len_frame,):
    # rotation
    rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
    len_joint = len(tgt_common_joints)
    for j in range(len_joint):
        # joint 
        src_joint = src_common_joints[j]
        tgt_joint = tgt_common_joints[j]

        template_index = tgt_joints_template_indices[j]
        subchain_indices = []
        if template_index!=-1:
            for chain in tgt_subchain_template_indices:
                if template_index in chain:
                    # chain에서 몇번째 인덱스
                    subjoint_jid = chain.index(template_index)
                    subchain_indices.append(subjoint_jid)
                    # print(f"joint {j} {tgt_joint} : subchain {subjoint_jid} {tgt_subchains[0][subjoint_jid]}")

        # Get source T-pose pre-rotation
        source_tpose_rot = src_Tpose_localrots[j]
        source_tpose_matrix = om.MEulerRotation(
            math.radians(source_tpose_rot[0]),
            math.radians(source_tpose_rot[1]),
            math.radians(source_tpose_rot[2]),
            om.MEulerRotation.kXYZ
        ).asMatrix()

        # Get target T-pose pre-rotation
        target_tpose_rot = tgt_Tpose_localrots[j]
        target_tpose_matrix = om.MEulerRotation(
            math.radians(target_tpose_rot[0]),
            math.radians(target_tpose_rot[1]),
            math.radians(target_tpose_rot[2]),
            om.MEulerRotation.kXYZ
        ).asMatrix()

        # retarget
        def set_keyframe_for_joint(tgt_joint, target_tpose_matrix, T_mat, jid):
            tgt_perjoint_local_angle = np.full((len_frame+1, 3), None, dtype=np.float32)
            prev_angles = np.zeros(3)
            for frame in range(len_frame):
                # source rotation
                cmds.currentTime(frame)
                source_rot = cmds.getAttr(f"{src_joint}.rotate")[0]
                source_matrix = om.MEulerRotation(
                    math.radians(source_rot[0]),
                    math.radians(source_rot[1]),
                    math.radians(source_rot[2]),
                    om.MEulerRotation.kXYZ
                ).asMatrix()

                # om mat
                convert_matric = matrix_to_mmatrix(T_mat)

                source_offset = source_matrix * source_tpose_matrix.inverse()
                converted_offset = convert_matric * source_offset * convert_matric.inverse()
                final_matrix = converted_offset * target_tpose_matrix

                # E_to_R 사용
                final_matrix = np.array(final_matrix).reshape(4, 4)
                euler_angle = R_to_E_(final_matrix)
                
                tgt_perjoint_local_angle[frame] = euler_angle 

            set_keyframe(tgt_joint, tgt_perjoint_local_angle, rot_attr)

        set_keyframe_for_joint(tgt_joint, target_tpose_matrix, Tpose_trfs[j], j)

        # subchain
        for chain_id, subjoint_jid in enumerate(subchain_indices):
            subjoint = tgt_subchains[chain_id][subjoint_jid]

            subjoint_tpose_rot = subchain_Tpose_localrots[subjoint_jid]
            subjoint_tpose_matrix = om.MEulerRotation(
                math.radians(subjoint_tpose_rot[0]),
                math.radians(subjoint_tpose_rot[1]),
                math.radians(subjoint_tpose_rot[2]),
                om.MEulerRotation.kXYZ
            ).asMatrix()

            set_keyframe_for_joint(subjoint, subjoint_tpose_matrix, subchain_Tpose_trfs[subjoint_jid], subjoint_jid) # is_subjoint=True
