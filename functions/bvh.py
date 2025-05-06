import maya.cmds as cmds
import re
import os 

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

    return grp