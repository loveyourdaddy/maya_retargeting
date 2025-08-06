import maya.cmds as cmds
import math
# import maya.OpenMaya as om
import maya.api.OpenMaya as om

from functions.joints import *
from functions.keyframe import *
from functions.character import *
from functions.rotations import *
from functions.maya import *


class RetargetingProcessor:
    """리타겟팅 처리를 위한 클래스"""
    
    def __init__(self, source_char, target_char):
        self.source = source_char
        self.target = target_char
        self.height_ratio = 1.0
        self.conversion_matrices = []
        self.subchain_conversion_matrices = []

    ''' joint common hierarchy '''
    def get_common_skeleton(self):
        """공통 스켈레톤 생성"""
        # 메인 체인 변환
        self.get_conversion()
        
        # 서브 체인 변환
        for j, subchain_joints in enumerate(self.target.subchains):
            subchain_joints_common, tgt_subchain_template_index, subchain_Tpose_rots_common, subchain_conversion_matrix \
             = self.get_conversion(
                is_subchain=True, 
                root_joint=self.target.subchain_template_roots[j], 
                subchain_joints=subchain_joints, 
                subchain_template=self.target.subchain_template[j], 
                subchain_template_indices=self.target.subchain_template_indices[j],
                )
            # import pdb; pdb.set_trace()
            
            self.target.subchain_joints_common.append(subchain_joints_common)
            self.target.subchain_template_indices[j] = tgt_subchain_template_index
            self.target.subchain_Tpose_rots_common.append(subchain_Tpose_rots_common)
            self.subchain_conversion_matrices.append(subchain_conversion_matrix)
    
    def get_conversion(self, 
                       is_subchain=False, 
                       root_joint=None, 
                       subchain_joints=None, subchain_template=None, subchain_template_indices=None, # subchain
                       ):
        if is_subchain==False:
            src_joints = self.source.joints
            src_joints_template = self.source.joints_template

            tgt_joints = self.target.joints
            tgt_joints_template = self.target.joints_template
            tgt_joints_template_indices = self.target.template_indices
        else:
            src_joints = self.source.joints
            src_joints_template = self.source.joints_template

            tgt_joints = subchain_joints
            tgt_joints_template = subchain_template
            tgt_joints_template_indices = subchain_template_indices
            

        """조인트 변환을 위한 공통 계층 구조 및 변환 매트릭스 생성"""
        # common hierarchy
        src_indices, tgt_indices = self.get_common_hierarchy_bw_src_and_tgt(
            src_joints, src_joints_template, # src 
            tgt_joints, tgt_joints_template, root_joint, # tgt 
            )
        
        # indices
        src_joints_common = [src_joints[i] for i in src_indices]
        tgt_joints_common = [tgt_joints[i] for i in tgt_indices]

        # indices 
        tgt_joints_template_indices = [tgt_joints_template_indices[i] for i in tgt_indices]

        # Tpose rot common
        tgt_Tpose_rots_common = get_Tpose_localrot(tgt_joints_common)
        src_Tpose_rots_common = get_Tpose_localrot(src_joints_common)

        # Tpose trf
        conversion_matrices = self.get_conversion_matrix(src_joints_common, tgt_joints_common)

        if is_subchain==False:
            self.source.joints_common = src_joints_common
            self.target.joints_common = tgt_joints_common
            self.source.Tpose_rots_common = src_Tpose_rots_common
            self.target.Tpose_rots_common = tgt_Tpose_rots_common
            self.conversion_matrices = conversion_matrices
        else:
            return tgt_joints_common, tgt_joints_template_indices, tgt_Tpose_rots_common, conversion_matrices

    def get_common_hierarchy_bw_src_and_tgt(
            self, 
            src_joints_origin, src_joints_template, 
            tgt_joints_origin, tgt_joints_template, root_joint=None):
        # jid, name
        tgt_root_div_jid, tgt_root_div, tgt_spine_div_jid, tgt_spine_div = get_division_by_name(tgt_joints_origin, tgt_joints_template, root_joint=root_joint)
        src_root_div_jid, src_root_div, src_spine_div_jid, src_spine_div = get_division_by_name(src_joints_origin, src_joints_template)

        # 만약 root joint을 찾을 수 없다면, 분기점으로 name을 바꿔주기
        if tgt_root_div_jid==-1:
            tgt_joints_template, tgt_root_div_jid, tgt_root_div, tgt_spine_div_jid, tgt_spine_div = \
                find_skeleton_by_hierarchy(tgt_joints_origin)

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

    def get_conversion_matrix(self, src_joint_hierarchy, tgt_joint_hierarchy):
        # x, y, z vector in world space
        def get_axis_vec_in_world_space(joint_name):
            matrix = cmds.xform(joint_name, query=True, worldSpace=True, matrix=True)
            m_matrix = om.MMatrix(matrix)
            transform = om.MTransformationMatrix(m_matrix)
            m_matrix = transform.asMatrix()

            # 각 축의 벡터 추출
            x_axis = np.array([m_matrix[0], m_matrix[1], m_matrix[2]])
            y_axis = np.array([m_matrix[4], m_matrix[5], m_matrix[6]])
            z_axis = np.array([m_matrix[8], m_matrix[9], m_matrix[10]])
            
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

    def identify_root_joints(self):
        """루트 관절 식별"""
        self.source.root_index = get_root_joint(self.source.joints_common)
        self.target.root_index = get_root_joint(self.target.joints_common)
        self.source.root = self.source.joints_common[self.source.root_index]
        self.target.root = self.target.joints_common[self.target.root_index]
        src_root = self.source.root
        tgt_root = self.target.root
        
        # 서브 체인이 있을 경우 root로 부터 상대적인 위치 계산
        self.target.calculate_relative_positions()
        
        return src_root, tgt_root
    
    def get_height_ratio(self):
        # 힙 높이 계산 
        src_toe = self.source.joints_common[-1] # TODO: get toe joint 
        tgt_toe = self.target.joints_common[-1]
        
        src_hip_height = self.source.get_distance_from_toe_to_root(src_toe)
        tgt_hip_height = self.target.get_distance_from_toe_to_root(tgt_toe)
        
        # 높이 비율 계산
        self.height_ratio = tgt_hip_height / src_hip_height

    
    """모션 리타겟팅 수행"""
    def retarget(self):
        # 로케이터 정보 확인
        has_locator = (self.source.locator is not None or self.target.locator is not None)
        
        if not has_locator:
            print(">> 로케이터 없이 리타겟팅")
            raise ValueError("로케이터가 없습니다")
        
        # 키프레임 데이터 가져오기
        trans_data, _ = get_keyframe_data(self.source.root)
        trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
        trans_data = get_array_from_keyframe_data(trans_data, trans_attr, self.source.root)
        len_frame = len(trans_data)
        self.len_frame = len_frame
        
        # retarget
        # 회전 리타겟팅
        tgt_local_angles = self.retarget_rotation()
        
        # 이동 리타겟팅
        trans_data = self.retarget_translation(
            trans_data, tgt_local_angles[:, self.source.root_index])
        
        return tgt_local_angles, trans_data
    
    def retarget_rotation(self):
        # elements
        src_common_joints = self.source.joints_common
        src_Tpose_localrots = self.source.Tpose_rots_common

        tgt_common_joints = self.target.joints_common
        tgt_Tpose_localrots = self.target.Tpose_rots_common
        tgt_joints_template_indices = self.target.template_indices
        Tpose_trfs = self.conversion_matrices

        # subchain 유무판단 
        retarget_with_subchain = len(self.target.subchains) > 0


        """회전 데이터 리타겟팅"""
        # rotation
        self.rot_attr = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
        len_joint = len(tgt_common_joints)
        len_frame = self.len_frame
        tgt_local_angles = np.full((len_frame, len_joint, 3), None, dtype=np.float32)
        
        for j in range(len_joint):
            # joint 
            self.src_joint = src_common_joints[j]
            self.tgt_joint = tgt_common_joints[j]

            # subjoint가 있는 경우, target joint의 index가 subchain에 있다면 subchain_indices에 포함
            if retarget_with_subchain:
                template_index = tgt_joints_template_indices[j]
                subchain_indices = []
                for subchain in self.target.subchain_template_indices:
                    if template_index in subchain:
                        # chain에서 몇번째 인덱스
                        subjoint_jid = subchain.index(template_index)
                        subchain_indices.append(subjoint_jid)

            # Get source T-pose pre-rotation
            source_tpose_rot = src_Tpose_localrots[j]
            self.source_tpose_matrix = om.MEulerRotation(
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

            # update
            tgt_perjoint_local_angle = self.set_keyframe_for_joint(self.tgt_joint, target_tpose_matrix, Tpose_trfs[j])
            tgt_local_angles[:, j] = tgt_perjoint_local_angle

            # subchain
            if retarget_with_subchain:
                for chain_id, subjoint_jid in enumerate(subchain_indices):
                    subjoint = self.target.subchains[chain_id][subjoint_jid]

                    subjoint_tpose_rot = self.target.subchain_Tpose_rots_common[chain_id][subjoint_jid]
                    subjoint_tpose_matrix = om.MEulerRotation(
                        math.radians(subjoint_tpose_rot[0]),
                        math.radians(subjoint_tpose_rot[1]),
                        math.radians(subjoint_tpose_rot[2]),
                        om.MEulerRotation.kXYZ
                    ).asMatrix()

                    self.set_keyframe_for_joint(subjoint, subjoint_tpose_matrix, self.subchain_conversion_matrices[chain_id][subjoint_jid])
            
        return tgt_local_angles
    
    # retarget
    def set_keyframe_for_joint(self, tgt_joint, target_tpose_matrix, T_mat): # , jid
        tgt_perjoint_local_angle = np.full((self.len_frame, 3), None, dtype=np.float32)
        for frame in range(self.len_frame):
            # source rotation
            cmds.currentTime(frame)
            source_rot = cmds.getAttr(f"{self.src_joint}.rotate")[0]
            source_rot = [source_rot[0], source_rot[1], source_rot[2]]

            source_matrix = om.MEulerRotation(
                math.radians(source_rot[0]),
                math.radians(source_rot[1]),
                math.radians(source_rot[2]),
                om.MEulerRotation.kXYZ
            ).asMatrix()

            # om mat
            convert_matric = matrix_to_mmatrix(T_mat)
            source_offset = source_matrix * self.source_tpose_matrix.inverse()
            converted_offset = convert_matric * source_offset * convert_matric.inverse()
            final_matrix = converted_offset * target_tpose_matrix

            # euler angle 
            final_matrix = np.array(final_matrix).reshape(4, 4)
            euler_angle = R_to_E(final_matrix, order='xyz') # MAYA rotation order: XYZ
            tgt_perjoint_local_angle[frame] = euler_angle
        
        # Refine angle as continue value
        tgt_perjoint_local_angle = self.unwrap_rotation(tgt_perjoint_local_angle)

        # update 
        set_keyframe(tgt_joint, tgt_perjoint_local_angle, self.rot_attr)

        return tgt_perjoint_local_angle
    
    def unwrap_rotation(self, rotation_array, threshold=170):
        """
        Euler angle discontinuity를 해결하여 연속적인 rotation 값으로 변환
        
        Args:
            rotation_array: shape (n, 3)의 rotation 데이터
            threshold: 불연속으로 간주할 각도 차이 (기본값: 170도)
        
        Returns:
            연속적인 값으로 변환된 rotation array
        """
        result = rotation_array.copy()
        
        # x, y, z 각 축별로 처리
        for axis in range(3):
            # 이전 프레임과의 차이 계산
            diff = np.diff(result[..., axis], axis=0)
            
            # 큰 변화가 있는 joint 찾기 (threshold 이상의 차이)
            discontinuities = np.where(np.abs(diff) > threshold)
            discont_frame = discontinuities[0]

            # 각 불연속 지점에 대해
            offset = 0
            for i, f in enumerate(discont_frame):

                # 부호 결정 (양수에서 음수로 가면 +360, 음수에서 양수로 가면 -360)
                if diff[f] < 0:  # 양수에서 음수로 갈 때
                    offset = 360
                else:  # 음수에서 양수로 갈 때
                    offset = -360
                
                # idx+1부터 끝까지의 모든 값에 offset 적용
                result[f+1:, axis] += offset
                
        return result

    def retarget_translation(self, 
                           trans_data, tgt_root_local_angles,
                        ):
        # subchain 유무판단 
        retarget_with_subchain = len(self.target.subchains) > 0

        """이동 데이터 리타겟팅"""
        trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
        len_frame = self.len_frame
        height_ratio = self.height_ratio

        # Source locator 처리
        if self.source.locator:
            src_loc_rotmat = get_rotation_matrix(self.source.locator_angle, len_frame)
            trans_data = apply_rotation(src_loc_rotmat, trans_data)
            trans_data = apply_scale(trans_data, self.source.locator_scale)

        # Target locator 처리
        if self.target.locator:
            tgt_loc_rotmat_inv = get_rotation_matrix(self.target.locator_angle, len_frame, inverse=True)
            trans_data = apply_rotation(tgt_loc_rotmat_inv, trans_data)
            
            # locator 포지션 반영
            if self.target.locator_pos is not None:
                tgt_pos = repeat_matrix(np.array(self.target.locator_pos), len_frame)
                if self.source.locator:
                    tgt_pos = apply_rotation(src_loc_rotmat, tgt_pos)
                tgt_pos = apply_rotation(tgt_loc_rotmat_inv, tgt_pos)
                trans_data = trans_data - tgt_pos
            
            # scale 
            trans_data = apply_scale(trans_data, self.target.locator_scale, inverse=True)

        # update 
        trans_data_main = trans_data * height_ratio
        set_keyframe(self.target.root, trans_data_main, trans_attr)

        # subchain
        if retarget_with_subchain:
            tgt_Tpose_root_angle = self.target.Tpose_rots_common[self.source.root_index]

            Tpose_root_R = E_to_R(np.array(tgt_Tpose_root_angle)) 
            Tpose_root_R_ext = np.repeat(Tpose_root_R[None, :], repeats=len_frame, axis=0)
            for i, subchain_root in enumerate(self.target.subchain_roots):
                root_R = E_to_R(tgt_root_local_angles)
                delta_R = np.linalg.inv(Tpose_root_R_ext) @ root_R
                # delta_R = root_R @ np.linalg.inv(Tpose_root_R_ext)

                diff_vec = self.target.subchain_local_diff_vec[i]
                # update diff vector
                diff_vec = self.target.subchain_local_diff_vec[i]
                diff_vec_ext = np.repeat(diff_vec[None,:], repeats=len_frame, axis=0)[:,:,None]
                delta_diff_vec = (delta_R @ diff_vec_ext)[:, :, 0]
                
                # update to subchain
                trans_data_sub = trans_data_main + delta_diff_vec
                set_keyframe(subchain_root, trans_data_sub, trans_attr)

        return trans_data

    """소스 객체 정리"""
    def cleanup_source(self):
        """소스 객체 정리"""
        # 소스 로케이터 및 조인트 삭제
        if self.source.locator is not None:
            self._delete_locator_and_hierarchy(self.source.locator)
        else:
            self._delete_locator_and_hierarchy(self.src_joints_common[0])
        
        # 메쉬 삭제
        remove_transform_node(self.source.meshes)
    
    def _delete_locator_and_hierarchy(self, node):
        """로케이터와 그 계층 구조 삭제"""
        if cmds.objExists(node):
            # 부모 노드 가져오기
            parent = cmds.listRelatives(node, parent=True)
            if parent:
                # 최상위 부모 노드 삭제
                while parent:
                    next_parent = cmds.listRelatives(parent[0], parent=True)
                    if not next_parent:
                        break
                    parent = next_parent
                
                if parent:
                    cmds.delete(parent[0])
            else:
                # 노드 자체 삭제
                cmds.delete(node)
    
    def rename_target_objects(self, tgt_joints_origin_woNS):
        """타겟 객체 이름 바꾸기"""
        # 조인트 이름 변경
        for joint in tgt_joints_origin_woNS:
            if len(joint.split(':')) > 1:
                # 타겟 이름에 네임스페이스가 있는 경우 네임스페이스 변경
                namespace = joint.split(':')[:-1][0] + ":"
                joint = joint.split(':')[-1]
                
                if cmds.objExists('tgt:' + joint):
                    cmds.rename('tgt:' + joint, namespace + joint)
            else:
                if cmds.objExists('tgt:' + joint):
                    cmds.rename('tgt:' + joint, joint)
        
        # 메쉬 이름 변경
        meshes = cmds.ls(type='mesh')
        transforms = []
        
        for mesh in meshes:
            parent = cmds.listRelatives(mesh, parent=True)
            if parent:
                transforms.append(parent[0])
        
        # 중복 제거
        transforms = list(set(transforms))
        
        # 변형 노드에서 네임스페이스 제거
        new_transforms = remove_namespace_from_objects(transforms)
        
        # 타겟 로케이터 이름 변경
        if self.target.locator is not None:
            self.target.locator_list = remove_namespace_for_joints(self.target.locator_list)[0]

