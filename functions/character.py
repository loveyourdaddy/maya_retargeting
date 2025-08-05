import maya.cmds as cmds
from functions.joints import *
from functions.keyframe import *
from functions.rotations import *
from functions.motion import *


class Character:
    """ 캐릭터 스켈레톤 및 메쉬 처리를 위한 클래스 """
    
    def __init__(self, name, namespace=""):
        self.name = name
        self.namespace = namespace
        self.joints = []
        self.joints_origin = []
        self.joints_template = []
        self.template_indices = []
        self.root_joints = []
        self.root_index = -1
        self.hip_height = 0
        self.meshes = []
        self.locator = None
        self.locator_angle = None
        self.locator_scale = None
        self.locator_pos = None
        self.locator_list = []
        
        # 서브 체인 관련 속성
        self.subchains = []
        self.subchain_template = []
        self.subchain_template_indices = []
        self.subchain_roots = []
        self.subchain_template_roots = []
        self.subchain_local_diff_vec = []
    
    """ tgt """
    def get_tgt_joints(self):
        """캐릭터의 관절 정보 추출"""
        # if self.namespace == "tgt":
        self.joints, self.joints_origin, self.chain_index, self.root_joints = self._get_tgt_joints()
        
        # 서브 체인 계산
        self._process_subchains()
        
        # 템플릿 조인트로 변환
        self.joints_template, _, self.template_indices = rename_joint_by_template(self.joints)
    
    def _get_tgt_joints(self):
        """타겟 캐릭터의 관절 정보 추출"""
        # 조인트 이름 중복 처리
        self._rename_duplicate_joints()
        
        # 모든 조인트 가져오기
        all_joints = cmds.ls(type='joint')
        
        # 네임스페이스가 없는 경우 처리
        joints_wo_ns = []
        for joint in all_joints:
            if ':' not in joint:
                joints_wo_ns.append(joint)
                continue
                
            # 네임스페이스가 있는 경우 타겟 네임스페이스인지 확인
            self.namespace = joint.split(':')[0]
            # if ns != self.namespace:
            #     continue
            
            joints_wo_ns.append(joint.split(':')[-1])
        
        # 타겟 조인트 추출 및 네임스페이스 추가
        tgt_joints_origin_woNS = copy.deepcopy(joints_wo_ns)
        tgt_joints_wNS = add_namespace_for_joints(joints_wo_ns, self.namespace)
        
        # 루트 조인트 찾기
        tgt_root_max_index, tgt_root_joints = find_root_joints(tgt_joints_wNS)
        
        return tgt_joints_wNS, tgt_joints_origin_woNS, tgt_root_max_index, tgt_root_joints
    
    def _rename_duplicate_joints(self):
        """씬에서 중복된 조인트 이름을 찾아서 새로운 이름으로 변경합니다."""
        # 씬의 모든 조인트를 가져옵니다
        all_joints = cmds.ls(type='joint', long=True)
        
        # 조인트의 짧은 이름을 저장할 딕셔너리
        joint_names = {}
        
        # 중복 이름을 찾습니다
        duplicates = []
        for joint in all_joints:
            # 전체 경로에서 짧은 이름만 추출
            short_name = joint.split('|')[-1]
            
            if short_name in joint_names:
                # 중복된 이름이 발견되면 리스트에 추가
                duplicates.append(joint)
            else:
                joint_names[short_name] = joint
        
        # 중복된 조인트들의 이름을 변경합니다 (중복된 조인트 중 뒤의 조인트)
        for duplicate in duplicates:
            short_name = duplicate.split('|')[-1]
            counter = 1
            
            # 새로운 이름이 고유할 때까지 숫자를 증가시킵니다
            while True:
                new_name = f"{short_name}_{counter}"
                if not cmds.objExists(new_name):
                    # 이름 변경 실행
                    if cmds.objExists(duplicate):
                        cmds.rename(duplicate, new_name)
                        break
                    if cmds.objExists(short_name):
                        # 일단 2개로 가정.
                        long_name = cmds.ls(short_name, long=True)[-1]
                        cmds.rename(long_name, new_name)
                        break

                counter += 1
    
    def _process_subchains(self):
        """서브 체인 처리"""
        # 타겟 조인트 리스트 구성
        tgt_joints_list = []
        tgt_parent_node_list = []
        
        for root_id, root in enumerate(self.root_joints):
            # 루트 업데이트
            root = f"{self.namespace}:" + root.split(":")[-1]
            
            # 조인트 계층 가져오기
            tgt_joints = get_joint_hierarchy(root)
            tgt_joints_list.append(tgt_joints)
            
            # 로케이터 가져오기
            try:
                parent_node = cmds.listRelatives(root, parent=True, shapes=True)[-1]
                tgt_parent_node_list.append(parent_node)
                
                if parent_node not in self.locator_list:
                    self.locator_list.append(parent_node)
                    self.locator_list.append(parent_node+'Shape')
            except (IndexError, TypeError):
                tgt_parent_node_list.append(None)
        
        # 추가 로케이터가 있다면 추가
        additional_locators_list = cmds.ls(type='locator')
        for additional_loctor in additional_locators_list:
            if additional_loctor not in self.locator_list:
                self.locator_list.append(additional_loctor)
                self.locator_list.append(additional_loctor+'Shape')
        
        # 타겟 조인트를 선택된 체인으로 변경
        parent_node = tgt_parent_node_list[self.chain_index]
        self.joints = tgt_joints_list[self.chain_index]
        
        # 서브 체인 구성
        for cid, joints in enumerate(tgt_joints_list):
            if cid == self.chain_index:
                continue
                
            self.subchains.append(joints)
            
            # 템플릿 인덱스
            chain_joints_template, _, template_indices = rename_joint_by_template(joints)
            self.subchain_template.append(chain_joints_template)
            self.subchain_template_indices.append(template_indices)
        
        # 서브 체인 루트
        for j, subchain in enumerate(self.subchains):
            self.subchain_roots.append(subchain[0])
            self.subchain_template_roots.append(self.subchain_template[j][0])
        
        # 로케이터 설정
        if parent_node is not None:
            self.locator, self.locator_angle, self.locator_scale, self.locator_pos = self._get_locator(parent_node)
            # 네임스페이스 추가
            self.locator = f"{self.namespace}:" + self.locator
        
        # 로케이터 리스트에 네임스페이스 추가
        self.locator_list = add_namespace_for_joints(self.locator_list, self.namespace)
    

    """ src """
    def get_src_joints(self, exception_joints=None):
        self._get_joints_wo_exception(exception_joints)
        self.joints_template, _, _ = rename_joint_by_template(self.joints)

    def _get_joints_wo_exception(self, exception_joints):
        joints = cmds.ls(type='joint')
        joints = list(set(joints) - set(exception_joints))
        idx, root_joints = find_root_joints(joints)
        root_joint = root_joints[idx]
        self.joints = get_joint_hierarchy(root_joint)

    # def _get_src_joints(self):
    #     """소스 캐릭터의 관절 정보 추출"""
    #     # 타겟 조인트에서 템플릿으로 매핑된 조인트 찾기
    #     template_joints = [joint for joint in self.joints_template if joint]
        
    #     # 소스 조인트 찾기
    #     src_joints = []
    #     all_joints = cmds.ls(type='joint')
        
    #     for joint in all_joints:
    #         if joint.startswith(f"{self.namespace}:"):
    #             continue
                
    #         # 조인트 추가
    #         src_joints.append(joint)
        
    #     return src_joints
    
    def _get_locator(self, locator):
        """로케이터 정보 추출"""
        # 회전값 가져오기
        locator_angle = cmds.xform(locator, query=True, rotation=True)
        # 스케일 가져오기
        locator_scale = cmds.xform(locator, query=True, scale=True)
        # 위치 가져오기
        locator_pos = cmds.xform(locator, query=True, translation=True)
        
        return locator, locator_angle, locator_scale, locator_pos
    
    def get_meshes(self):
        """메쉬 정보 추출"""
        if self.namespace == "tgt":
            self.meshes = cmds.ls(type='mesh')
            self.meshes = add_namespace_for_meshes(self.meshes, self.namespace)
        else:
            # 타겟 메쉬와 차집합으로 소스 메쉬 찾기
            all_meshes = cmds.ls(type='mesh')
            self.meshes = [mesh for mesh in all_meshes if not mesh.startswith('tgt:')]
    
    def calculate_relative_positions(self, main_root):
        """서브 체인의 상대 위치 계산"""
        hip_local_pos = np.array(cmds.xform(main_root, query=True, translation=True, worldSpace=False))
        
        for root in self.subchain_roots:
            sub_hip_local_pos = np.array(cmds.xform(root, query=True, translation=True, worldSpace=False))
            local_diff_vec = sub_hip_local_pos - hip_local_pos
            self.subchain_local_diff_vec.append(local_diff_vec)
    
    def get_distance_from_toe_to_root(self, root, toe):
        toe_pos = cmds.xform(toe, query=True, translation=True, worldSpace=True)
        root_pos = cmds.xform(root, query=True, translation=True, worldSpace=True)
        
        # 발끝에서 루트까지의 수직 거리를 계산합니다.
        y_component = 1
        hip_height = root_pos[y_component] - toe_pos[y_component]
        return hip_height


''' joint hierarchy ''' 
# TODO
def update_root_to_locator_rotation(tgt_joints_origin, tgt_root, tgt_locator_angle):
    # 조인트들: root joint -> locator
    index = tgt_joints_origin.index(tgt_root)
    parent_rotation = np.eye(3)
    parent_joint = cmds.listRelatives(tgt_joints_origin[index], parent=True, shapes=True)[0]

    # get parent: Root -> locator
    while(parent_joint in tgt_joints_origin):
        # get rotation 
        parent_index = tgt_joints_origin.index(parent_joint)
        rotation = get_localrot_of_joint(tgt_joints_origin[parent_index])
        parent_rotation = parent_rotation @ rotation # parent은 오른쪽에 곱함

        # parent index 
        index = parent_index
        parent_joint = cmds.listRelatives(tgt_joints_origin[index], parent=True, shapes=True)[0]

    # E to R
    tgt_locator_rot = E_to_R(np.array(tgt_locator_angle))
    tgt_locator_rot = parent_rotation @ tgt_locator_rot
    updated_locator_angle = R_to_E(tgt_locator_rot)
    return updated_locator_angle