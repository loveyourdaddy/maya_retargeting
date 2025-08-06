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

        # joints 
        self.joints = []
        self.joints_origin = []
        self.joints_template = []
        self.template_indices = [] # template joint에 따른 index (없다면 -1)

        # Relationship between source and target
        # joint common 
        self.joints_common = []
        self.joint_indices_common = []
        # Tpose rot (default rotation)
        self.Tpose_rots_common = []
        
        # root 
        self.root = []
        self.root_joints = []
        self.root_index = -1
        self.hip_height = 0
        
        # locator
        self.locator = None
        self.locator_angle = None
        self.locator_scale = None
        self.locator_pos = None
        self.locator_list = []
        
        # subchain 관련 속성
        self.subchains = []
        self.subchain_template = []
        self.subchain_template_indices = [] # 
        self.subchain_roots = []
        self.subchain_template_roots = []
        self.subchain_local_diff_vec = []

        # subchain common
        self.subchain_joints_common = []
        self.subchain_joint_indices_common = []
        # Tpose rot (default rotation)
        self.subchain_Tpose_rots_common = []

        # mesh
        self.meshes = []
    
    """ tgt """
    def get_tgt_joints(self):
        """캐릭터의 관절 정보 추출. target 캐릭터에 subchain이 있을 경우만 리타게팅함"""
        # main joints
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

    """ Get info """
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
    
    def calculate_relative_positions(self, ):
        """서브 체인의 상대 위치 계산"""
        hip_local_pos = np.array(cmds.xform(self.root, query=True, translation=True, worldSpace=False))
        
        for root in self.subchain_roots:
            sub_hip_local_pos = np.array(cmds.xform(root, query=True, translation=True, worldSpace=False))
            local_diff_vec = sub_hip_local_pos - hip_local_pos
            self.subchain_local_diff_vec.append(local_diff_vec)
    
    def get_distance_from_toe_to_root(self, toe):
        toe_pos = cmds.xform(toe, query=True, translation=True, worldSpace=True)
        root_pos = cmds.xform(self.root, query=True, translation=True, worldSpace=True)
        
        # 발끝에서 루트까지의 수직 거리를 계산합니다.
        y_component = 1
        hip_height = root_pos[y_component] - toe_pos[y_component]
        return hip_height

    """ Refine """
    def refine_locator_rotation(self):
        """로케이터 회전 정제"""
        if self.locator is not None:
            self.locator_angle = self.update_root_to_locator_rotation()

    def update_root_to_locator_rotation(self):
        """ locator가 여러개 있을 경우를 대비해서, hip 바로위 locator ~ 가장 위쪽의 locator까지의 회전을 적용합니다 """
        joints = self.joints 

        # 조인트들: root joint -> locator
        index = joints.index(self.root)
        parent_rotation = np.eye(3)
        parent_joint = cmds.listRelatives(joints[index], parent=True, shapes=True)[0]

        # get parent: Root -> locator
        while(parent_joint in joints):
            # get rotation 
            parent_index = joints.index(parent_joint)
            rotation = get_localrot_of_joint(joints[parent_index])
            parent_rotation = parent_rotation @ rotation # parent은 오른쪽에 곱함

            # parent index 
            index = parent_index
            parent_joint = cmds.listRelatives(joints[index], parent=True, shapes=True)[0]

        # E to R
        tgt_locator_rot = E_to_R(np.array(self.locator_angle))
        tgt_locator_rot = parent_rotation @ tgt_locator_rot
        updated_locator_angle = R_to_E(tgt_locator_rot)
        return updated_locator_angle

""" skeleton hierarchy  """
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

def check_joint_by_template_names(joint_name, template_names):
    for template_name in template_names:
        if joint_name.lower() in template_name.lower() or template_name.lower() in joint_name.lower():
            return True
    return False