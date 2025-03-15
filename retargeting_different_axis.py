# Adori Asooni Metahuman UE
# mayapy retargeting_different_axis.py --sourceChar "./models/Asooni/Asooni.fbx" --sourceMotion "./motions/Asooni/Supershy.fbx" --targetChar "./models/Adori/Adori.fbx"
# mayapy retargeting_different_axis.py --sourceChar "./models/Adori/Adori.fbx" --sourceMotion "./motions/Adori/Nonsense_RT0227.fbx" --targetChar "./models/Asooni/Asooni.fbx"

''' 
Naming
원본 이름 
tgt_joints_real_origin

namespace 수정됨
tgt_joints_wNS: 원본 hierarchy, 네임스페이스만 바뀐것. 
tgt_joints_template: 원본 Hier, template joint만 renamed된것
tgt_joints_common: Hierarchy가 바뀐것.
'''

import maya.cmds as cmds
import maya.standalone
from functions.parser import *
from functions.character import *
from functions.motion import *
from functions.maya import *
from functions.retarget import *
import time
import re

class Joint:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.full_path = f"{parent.full_path}|{name}" if parent else name

def create_keyframe(channel, frame, value):
    """각 채널에 대한 키프레임 생성"""
    try:
        cmds.setKeyframe(channel, time=frame, value=float(value))
    except Exception as e:
        print(f"키프레임 생성 오류 - 채널: {channel}, 프레임: {frame}, 값: {value}")
        print(f"오류 메시지: {e}")
        
def parse_channels(line, joint_name):
    """채널 정보 파싱"""
    translation_dict = {
        'Xposition': 'translateX',
        'Yposition': 'translateY',
        'Zposition': 'translateZ',
        'Xrotation': 'rotateX',
        'Yrotation': 'rotateY',
        'Zrotation': 'rotateZ'
    }
    
    space_re = re.compile(r"\s+")
    chan_info = space_re.split(line.strip())
    channels = []
    
    for i in range(int(chan_info[1])):
        channel_type = chan_info[2 + i]
        maya_attr = translation_dict.get(channel_type)
        if maya_attr:
            channels.append(f"{joint_name}.{maya_attr}")
    
    return channels

def import_bvh(file_path, scale=1.0, frame_offset=0, rotation_order=0):
    """BVH 파일을 Maya로 임포트하고 키프레임 생성"""
    channels = []
    motion = False
    safe_close = False
    space_re = re.compile(r"\s+")
    current_joint = None
    
    with open(file_path) as f:
        # BVH 파일 유효성 검사
        if not f.readline().startswith("HIERARCHY"):
            raise ValueError("유효하지 않은 BVH 파일입니다")

        # 루트 그룹 생성
        mocap_name = os.path.basename(file_path)
        grp = cmds.group(em=True, name=f"_mocap_{mocap_name}_grp")
        cmds.setAttr(f"{grp}.scale", scale, scale, scale)
        root_group = Joint(grp)
        current_joint = root_group
        
        frame_data = []  # 모션 데이터 저장
        
        for line in f:
            line = line.replace("\t", " ").strip()
            
            if not motion:
                if line.startswith("ROOT"):
                    joint_name = line[5:].strip()
                    joint_name = joint_name.split('|')[-1]
                    
                    # 기존 조인트 검색 또는 새로 생성
                    existing_joints = cmds.ls(joint_name, type='joint', long=True)
                    maya_joint = existing_joints[0] if existing_joints else cmds.joint(name=joint_name, p=(0, 0, 0))
                    maya_joint = maya_joint.split('|')[-1]
                    
                    current_joint = Joint(maya_joint, current_joint)
                    cmds.setAttr(f"{current_joint.name}.rotateOrder", rotation_order)

                elif "JOINT" in line:
                    joint_name = space_re.split(line)[1].split('|')[-1]
                    
                    existing_joints = cmds.ls(joint_name, type='joint', long=True)
                    maya_joint = existing_joints[0] if existing_joints else cmds.joint(name=joint_name, p=(0, 0, 0))
                    maya_joint = maya_joint.split('|')[-1]
                    
                    current_joint = Joint(maya_joint, current_joint)
                    cmds.setAttr(f"{current_joint.name}.rotateOrder", rotation_order)

                elif "End Site" in line:
                    safe_close = True

                elif "}" in line:
                    if safe_close:
                        safe_close = False
                        continue
                    if current_joint and current_joint.parent:
                        current_joint = current_joint.parent
                        if current_joint:
                            cmds.select(current_joint.name)

                elif "CHANNELS" in line:
                    channels.extend(parse_channels(line, current_joint.name))
                    
                elif "MOTION" in line:
                    motion = True
            else:
                if "Frame Time:" in line:
                    continue
                if "Frames:" in line:
                    continue
                    
                # 모션 데이터 처리
                data = space_re.split(line)
                if len(data) > 1:  # 유효한 데이터 라인인지 확인
                    frame_data.append(data)
        
        # 키프레임 생성
        for frame_idx, data in enumerate(frame_data):
            for chan_idx, value in enumerate(data):
                # if frame_idx==60:
                #     import pdb; pdb.set_trace()
                if chan_idx < len(channels):
                    create_keyframe(channels[chan_idx], frame_idx + frame_offset, value)

        # # 조인트별로 채널 그룹화
        # joint_channels = {}
        # for channel in channels:
        #     joint_name = channel.split('.')[0]
        #     if joint_name not in joint_channels:
        #         joint_channels[joint_name] = []
        #     joint_channels[joint_name].append(channel)

        # # 각 프레임에 대해
        # for frame_idx, data in enumerate(frame_data):
        #     data_idx = 0
        #     # 각 조인트에 대해
        #     for joint_name, joint_chans in joint_channels.items():
        #         # XYZ 순서로 채널 정렬
        #         sorted_channels = []
                
        #         # Position channels (XYZ)
        #         for axis in ['translateX', 'translateY', 'translateZ']:
        #             for channel in joint_chans:
        #                 if axis in channel:
        #                     sorted_channels.append(channel)
                
        #         # Rotation channels (XYZ)
        #         for axis in ['rotateX', 'rotateY', 'rotateZ']:
        #             for channel in joint_chans:
        #                 if axis in channel:
        #                     sorted_channels.append(channel)
                
        #         # 정렬된 채널에 대해 키프레임 생성
        #         for channel in sorted_channels:
        #             if data_idx < len(data):
        #                 value = data[data_idx]
        #                 create_keyframe(channel, frame_idx + frame_offset, value)
        #                 data_idx += 1

    return grp

def import_motion_file(file_path, scale=1.0):
    """Import motion file (FBX or BVH)"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.fbx':
        mel.eval('FBXImport -f"{}"'.format(file_path))
    elif file_ext == '.bvh':
        return import_bvh(file_path, scale=scale)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

def main():
    start_time = time.time()
    maya.standalone.initialize(name='python')

    # Load the FBX plugin
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        cmds.loadPlugin('fbxmaya')
    
    # name
    args = get_args()
    # tgt
    targetChar = get_name(args.targetChar)
    targetMotion = get_name(args.sourceMotion)
    # src
    sourceMotion = args.sourceMotion
    sourceChar = sourceMotion.split('/')[-2]
    print(">> Source: ({}, {}) -> Target: {}".format(sourceChar, sourceMotion, targetChar))


    ''' Target '''
    # character
    mel.eval('FBXImportSmoothingGroups -v true')
    mel.eval('FBXImport -f"{}"'.format(args.targetChar))
    # .fbm 폴더 경로
    path = "./models/" + targetChar + "/" + targetChar
    fbm_folder = path + ".fbm"
    
    # import texture
    # 모든 파일 노드 가져오기
    file_nodes = cmds.ls(type="file")
    for node in file_nodes:
        # 현재 파일 경로 가져오기
        new_path = os.path.join(fbm_folder, node)
        
        # 새 경로가 존재하는지 확인
        if os.path.exists(new_path):
            # 텍스처 경로 업데이트
            cmds.setAttr(node + ".fileTextureName", new_path, type="string")
            # print(f">>Texture loaded: {node} -> {new_path}")
        else:
            print(f">>No texture: {new_path}")

    # joints
    tgt_joints_wNS, tgt_joints_origin_woNS, tgt_chain_index, tgt_root_joints = get_tgt_joints()
    
    # locator list
    tgt_locator_list = []
    tgt_joints_list = []
    tgt_parent_node_list = []
    for root_id, root in enumerate(tgt_root_joints):
        # update root 
        root = "tgt:" + root.split(":")[-1]
        
        # joints
        tgt_joints = get_joint_hierarchy(root)
        tgt_joints_list.append(tgt_joints)
        
        # locator 
        locator = cmds.listRelatives(root, parent=True, shapes=True)[-1]
        tgt_locator_list.append(locator)
        tgt_locator_list.append(locator+'Shape')

        parent_node = cmds.listRelatives(root, parent=True, shapes=True)[-1]
        tgt_parent_node_list.append(parent_node)

    # 다른 locator가 있다면 추가해주기
    additional_locators_list = cmds.ls(type='locator')
    for additional_loctor in additional_locators_list:
        if additional_loctor not in tgt_locator_list:
            tgt_locator_list.append(additional_loctor)
            tgt_locator_list.append(additional_loctor+'Shape')
    
    # 타겟 조인트를 selected chain으로 변경
    parent_node = tgt_parent_node_list[tgt_chain_index]
    tgt_joints_wNS = tgt_joints_list[tgt_chain_index]
    
    # joint templated
    tgt_joints_template, _, tgt_joints_template_indices = rename_joint_by_template(tgt_joints_wNS)

    # sub chain
    # 다른 chaing에 대해서 main skeleton을 찾기
    tgt_subchains = []
    tgt_subchain_template = []
    tgt_subchain_template_indices = []
    for cid, joints in enumerate(tgt_joints_list):
        if cid==tgt_chain_index:
            continue
        tgt_subchains.append(joints)
        
        # index 
        chain_joints_template, _, template_indices = rename_joint_by_template(joints)
        tgt_subchain_template.append(chain_joints_template)
        tgt_subchain_template_indices.append(template_indices)

    # subchain root
    subchain_roots = []
    subchain_template_roots = []
    for j, subchain in enumerate(tgt_subchains):
        subchain_roots.append(subchain[0])
        subchain_template_roots.append(tgt_subchain_template[j][0])
    
    # locator
    if parent_node is not None:
        tgt_locator, tgt_locator_angle, tgt_locator_scale, tgt_locator_pos = get_locator(parent_node)
        # add namespace
        tgt_locator = "tgt:" + tgt_locator
    else:
        tgt_locator = None

    # rename locator
    tgt_locator_list = add_namespace_for_joints(tgt_locator_list, "tgt")
    
    # meshes
    tgt_meshes = cmds.ls(type='mesh')
    tgt_meshes = add_namespace_for_meshes(tgt_meshes, "tgt")


    ''' Source char '''
    sourceChar_path = './models/' + sourceChar + '/' + sourceChar + '.fbx'

    # import source character
    if os.path.exists(sourceChar_path)==False:
        # source character가 없을때, 0 frame을 Tpose로 사용.
        print(">> no source character")
        raise ValueError("No source character")
    
    mel.eval('FBXImport -f"{}"'.format(sourceChar_path))

    # # rename src meshes
    all_meshes = cmds.ls(type='mesh')
    src_meshes = list(set(all_meshes) - set(tgt_meshes))
    # refine src_meshes
    src_meshes = [mesh for mesh in src_meshes if not mesh.startswith('tgt:')]


    src_joints_origin = get_src_joints(tgt_joints_wNS)
    src_joints_template, _, _ = rename_joint_by_template(src_joints_origin)

    # locator
    locators_list = cmds.ls(type='locator')
    src_locator_list = list(set(locators_list) - set(tgt_locator_list))
    if len(src_locator_list)!=0:
        # Select right locator
        src_locator_list = sorted(src_locator_list, key=lambda x: len(cmds.listRelatives(x, children=True) or []), reverse=True)
        
        # src locator선택: namespace tgt가 없는 경우
        src_locator_candidate = [] 
        for locator in src_locator_list:
            if locator.split(':')[0] != 'tgt':
                src_locator_candidate.append(locator)

        # 가장 많은 자식을 가진 locator를 선택하기 위해 0을 선택
        src_locator = src_locator_candidate[0]

        # Get locator info 
        src_locator, src_locator_angle, src_locator_scale, src_locator_pos = get_locator(src_locator)
    else:
        src_locator = None


    ''' Common skeleton '''
    # common joint 
    src_joints_common, src_Tpose_rots_common, \
    tgt_joints_common, tgt_Tpose_rots_common, tgt_joints_template_indices, \
    conversion_matrics \
        = get_conversion(
            src_joints_origin, src_joints_template, 
            tgt_joints_wNS, tgt_joints_template, tgt_joints_template_indices)

    # for subchain joints 
    subchain_conversion_matrics = []
    tgt_subchain_template_indices_refined = []
    subchain_common_joints = []
    subchain_Tpose_rots_common = []
    for j, subchain_joints in enumerate(tgt_subchains):
        _, _, \
        subchain_joints_common, subchain_Tpose_rots_common, tgt_subchain_template_index, \
        subchain_conversion_matrics \
            = get_conversion(
                src_joints_origin, src_joints_template, 
                subchain_joints, tgt_subchain_template[j], tgt_subchain_template_indices[j], 
                root_joint=subchain_template_roots[j])
        subchain_common_joints.append(subchain_joints_common)
        tgt_subchain_template_indices_refined.append(tgt_subchain_template_index)
        subchain_conversion_matrics.append(subchain_conversion_matrics)
    tgt_subchain_template_indices = tgt_subchain_template_indices_refined
    
    # root
    src_hip_index = get_root_joint(src_joints_common)
    tgt_hip_index = get_root_joint(tgt_joints_common)
    src_root = src_joints_common[src_hip_index]
    tgt_root = tgt_joints_common[tgt_hip_index]
    # hip height
    src_hip_height = get_distance_from_toe_to_root(src_joints_common, src_root)
    tgt_hip_height = get_distance_from_toe_to_root(tgt_joints_common, tgt_root)

    # ratio
    height_ratio = tgt_hip_height / src_hip_height

    # subchain
    # position
    hip_local_pos = np.array(cmds.xform(tgt_root, query=True, translation=True, worldSpace=False))
    # diff vec wo root rotation
    subchain_local_diff_vec = []
    for root in subchain_roots:
        sub_hip_local_pos = np.array(cmds.xform(root, query=True, translation=True, worldSpace=False))
        local_diff_vec = sub_hip_local_pos - hip_local_pos
        subchain_local_diff_vec.append(local_diff_vec)


    ''' Source motion '''
    import_motion_file(sourceMotion)

    # Set fps of source motion
    current_fps = mel.eval('currentTimeUnitToFPS')
    mel.eval(f'currentUnit "{current_fps}fps"') 
    print("fps: ", current_fps)

    ''' Refine locator rotation '''
    if tgt_locator is not None:
        # locator ~ root 위 조인트 포함
        tgt_locator_angle = update_root_to_locator_rotation(tgt_joints_wNS, tgt_root, tgt_locator_angle)


    ''' Retarget '''
    if src_locator is not None or tgt_locator is not None:
        # 둘 중 하나라도 locator가 있는 경우 
        # 예외처리
        if src_locator is None:
            src_locator_angle, src_locator_scale = None, None
        if tgt_locator is None:
            tgt_locator_angle, tgt_locator_scale = None, None
        
        # Get data
        trans_data, _ = get_keyframe_data(src_root) # trans, rot 
        trans_attr = {'translateX': [], 'translateY': [], 'translateZ': []}
        trans_data = get_array_from_keyframe_data(trans_data, trans_attr, src_root)
        len_frame = len(trans_data)

        # rot
        tgt_local_angles = retarget_rotation(src_joints_common, src_Tpose_rots_common,
                          tgt_joints_common, tgt_Tpose_rots_common, tgt_joints_template_indices, conversion_matrics, 
                          subchain_common_joints, subchain_Tpose_rots_common, tgt_subchain_template_indices, subchain_conversion_matrics,
                          len_frame)
        
        # trans
        trans_data = retarget_translation(src_root, tgt_root, 
                                          trans_data, tgt_local_angles[:, src_hip_index], tgt_Tpose_rots_common[src_hip_index],
                                          subchain_roots,
                                          src_locator, src_locator_angle, src_locator_scale,
                                          tgt_locator, tgt_locator_angle, tgt_locator_scale, tgt_locator_pos,
                                            height_ratio, subchain_local_diff_vec, 
                                            len_frame)
    else:
        print(">> retarget without locator")
        raise ValueError("No locator") # TODO
    
    ''' export '''
    # Remove source
    # source locator and joints
    if src_locator is not None:
        delete_locator_and_hierarchy(src_locator)
    else:
        delete_locator_and_hierarchy(src_joints_common[0])
    #  meshes
    remove_transform_node(src_meshes)


    # Rename tgt 
    # joint
    for joint in tgt_joints_origin_woNS:
        if len(joint.split(':'))>1:
            # 만약 target name에 namespace가 있다면 change namespace
            namespace = joint.split(':')[:-1][0] + ":"
            joint = joint.split(':')[-1]
            # 만약 조인트가 존재한다면 
            if cmds.objExists('tgt:'+joint):
                cmds.rename('tgt:'+joint, namespace+joint)
        else:
            if cmds.objExists('tgt:'+joint):
                cmds.rename('tgt:'+joint, joint)

    # mesh 
    # 변형 노드 가져오기
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
    
    # rename tgt locat
    tgt_locator_list = remove_namespace_for_joints(tgt_locator_list)[0]


    # export
    print(">> Source: ({}, {}) -> Target: {}".format(sourceChar, sourceMotion, targetChar))
    export(args, targetChar, targetMotion)
    
    # end
    maya.standalone.uninitialize()

    # end time
    end_time = time.time()
    execution_time = end_time - start_time
    minutes = int(execution_time // 60)
    seconds = execution_time % 60
    print(f">> Execution time: {execution_time:.3f}, ({minutes}m {seconds:.3f}s)")

if __name__=="__main__":
    main()
