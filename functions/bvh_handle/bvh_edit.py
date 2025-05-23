"""
python functions/bvh_handle/bvh_edit.py
BVH Joint Value Modifier - 특정 조인트의 특정 프레임 값을 변경하는 도구
"""

def analyze_bvh_structure(input_file):
    """
    BVH 파일의 구조를 분석하여 조인트 정보를 출력합니다.
    """
    with open(input_file, 'r') as f:
        lines = f.readlines()

    hierarchy_index = -1
    motion_index = -1
    
    for i, line in enumerate(lines):
        if line.strip() == 'HIERARCHY':
            hierarchy_index = i
        elif line.strip() == 'MOTION':
            motion_index = i
            break
    
    if hierarchy_index == -1 or motion_index == -1:
        raise ValueError("BVH 파일에서 HIERARCHY 또는 MOTION 섹션을 찾을 수 없습니다")
    
    joint_info = []
    current_joint = -1
    channel_start = 0
    
    for i in range(hierarchy_index, motion_index):
        line = lines[i].strip()
        if line.startswith('JOINT') or line.startswith('ROOT'):
            current_joint += 1
            joint_name = line.split()[1] if len(line.split()) > 1 else f"Joint_{current_joint}"
        elif line.startswith('CHANNELS'):
            parts = line.split()
            num_channels = int(parts[1])
            channels = parts[2:] if len(parts) > 2 else []
            
            joint_info.append({
                'index': current_joint,
                'name': joint_name,
                'channels': num_channels,
                'channel_names': channels,
                'start_index': channel_start
            })
            
            # print(f"조인트 {current_joint:2d}: {joint_name:15s} - 채널 {num_channels}개 ({' '.join(channels)}) - 인덱스 {channel_start}~{channel_start + num_channels - 1}"
            channel_start += num_channels
    
    return joint_info

def modify_joint_values(input_file, output_file, joint_index, start_frame, end_frame, new_values):
    """
    BVH 파일에서 특정 조인트의 특정 프레임 범위의 값을 변경합니다.
    
    Args:
        input_file (str): 입력 BVH 파일 경로
        output_file (str): 출력 BVH 파일 경로
        joint_index (int): 변경할 조인트 인덱스 (0부터 시작)
        start_frame (int): 시작 프레임 (0부터 시작)
        end_frame (int): 끝 프레임 (포함)
        new_values (list): 새로운 값들 [x, y, z] 또는 [rx, ry, rz]
    """
    # BVH 파일 읽기
    with open(input_file, 'r') as f:
        lines = f.readlines()

    # HIERARCHY와 MOTION 섹션 찾기
    hierarchy_index = -1
    motion_index = -1
    frames_index = -1
    num_frames = 0
    
    for i, line in enumerate(lines):
        if line.strip() == 'HIERARCHY':
            hierarchy_index = i
        elif line.strip() == 'MOTION':
            motion_index = i
        elif motion_index != -1 and line.strip().startswith('Frames:'):
            frames_line = line.strip()
            num_frames = int(frames_line.split(':')[1].strip())
            frames_index = i + 2  # 'Frames:'와 'Frame Time:' 라인을 건너뛰기
    
    if hierarchy_index == -1 or motion_index == -1 or frames_index == -1:
        raise ValueError("BVH 파일에서 HIERARCHY 또는 MOTION 섹션을 찾을 수 없습니다")
    
    # 조인트 구조 분석 (각 조인트가 몇 개의 채널을 가지는지 확인)
    joint_channels = []
    joint_names = []
    current_joint = -1
    
    for i in range(hierarchy_index, motion_index):
        line = lines[i].strip()
        if line.startswith('JOINT') or line.startswith('ROOT'):
            current_joint += 1
            joint_name = line.split()[1] if len(line.split()) > 1 else f"Joint_{current_joint}"
            joint_names.append(joint_name)
        elif line.startswith('CHANNELS'):
            parts = line.split()
            num_channels = int(parts[1])
            joint_channels.append(num_channels)
    
    # 지정된 조인트의 시작 인덱스 계산
    if joint_index >= len(joint_channels):
        raise ValueError(f"조인트 인덱스 {joint_index}가 범위를 벗어났습니다. 총 조인트 수: {len(joint_channels)}")
    
    joint_start_index = sum(joint_channels[:joint_index])
    joint_num_channels = joint_channels[joint_index]
    
    print(f"조인트 {joint_index} ({joint_names[joint_index]}):")
    print(f"  - 시작 인덱스: {joint_start_index}")
    print(f"  - 채널 수: {joint_num_channels}")
    print(f"  - 프레임 범위: {start_frame} ~ {end_frame}")
    print(f"  - 새 값: {new_values}")
    
    # 새 값의 개수가 조인트의 채널 수와 일치하는지 확인
    if len(new_values) != joint_num_channels:
        raise ValueError(f"새 값의 개수({len(new_values)})가 조인트의 채널 수({joint_num_channels})와 일치하지 않습니다")
    
    # 프레임 범위 검증
    if start_frame < 0 or end_frame >= num_frames or start_frame > end_frame:
        raise ValueError(f"프레임 범위가 잘못되었습니다. 유효 범위: 0 ~ {num_frames-1}")
    
    # 각 프레임의 데이터 수정
    modified_frames = 0
    for frame_idx in range(num_frames):
        line_idx = frames_index + frame_idx
        if line_idx >= len(lines) or not lines[line_idx].strip():
            continue
            
        # 현재 프레임이 수정 범위에 포함되는지 확인
        if start_frame <= frame_idx <= end_frame:
            # 들여쓰기 보존
            indent = lines[line_idx][:len(lines[line_idx]) - len(lines[line_idx].lstrip())]
            data = lines[line_idx].strip().split()
            
            if len(data) < joint_start_index + joint_num_channels:
                print(f"경고: 프레임 {frame_idx}의 데이터가 부족합니다")
                continue
            
            # 지정된 조인트의 값들을 새 값으로 교체
            print(f"프레임 {frame_idx}의 조인트 {joint_index} ({joint_names[joint_index]}) 채널 {joint_start_index}~{joint_start_index + joint_num_channels - 1}: {data[joint_start_index:joint_start_index + joint_num_channels]} -> {new_values}")
            for i, new_value in enumerate(new_values):
                data[joint_start_index + i] = str(new_value)
            
            # 수정된 라인으로 교체
            lines[line_idx] = indent + " ".join(data) + "\n"
            modified_frames += 1
    
    # 수정된 BVH 파일 저장
    with open(output_file, 'w') as f:
        f.writelines(lines)
    
    print(f"성공적으로 {modified_frames}개 프레임이 수정되어 {output_file}에 저장되었습니다")


def copy_joint_values(input_file, output_file, joint_index, source_frame, start_frame, end_frame):
    """
    BVH 파일에서 특정 조인트의 한 프레임 값을 다른 프레임 범위로 복사합니다.
    
    Args:
        input_file (str): 입력 BVH 파일 경로
        output_file (str): 출력 BVH 파일 경로
        joint_index (int): 복사할 조인트 인덱스 (0부터 시작)
        source_frame (int): 복사할 소스 프레임 (0부터 시작)
        start_frame (int): 붙여넣을 시작 프레임 (0부터 시작)
        end_frame (int): 붙여넣을 끝 프레임 (포함)
    """
    
    # BVH 파일 읽기
    with open(input_file, 'r') as f:
        lines = f.readlines()

    # HIERARCHY와 MOTION 섹션 찾기
    hierarchy_index = -1
    motion_index = -1
    frames_index = -1
    num_frames = 0
    
    for i, line in enumerate(lines):
        if line.strip() == 'HIERARCHY':
            hierarchy_index = i
        elif line.strip() == 'MOTION':
            motion_index = i
        elif motion_index != -1 and line.strip().startswith('Frames:'):
            frames_line = line.strip()
            num_frames = int(frames_line.split(':')[1].strip())
            frames_index = i + 2  # 'Frames:'와 'Frame Time:' 라인을 건너뛰기
    
    if hierarchy_index == -1 or motion_index == -1 or frames_index == -1:
        raise ValueError("BVH 파일에서 HIERARCHY 또는 MOTION 섹션을 찾을 수 없습니다")
    
    # 조인트 구조 분석
    joint_channels = []
    joint_names = []
    current_joint = -1
    
    for i in range(hierarchy_index, motion_index):
        line = lines[i].strip()
        if line.startswith('JOINT') or line.startswith('ROOT'):
            current_joint += 1
            joint_name = line.split()[1] if len(line.split()) > 1 else f"Joint_{current_joint}"
            joint_names.append(joint_name)
        elif line.startswith('CHANNELS'):
            parts = line.split()
            num_channels = int(parts[1])
            joint_channels.append(num_channels)
    
    # 지정된 조인트의 시작 인덱스 계산
    if joint_index >= len(joint_channels):
        raise ValueError(f"조인트 인덱스 {joint_index}가 범위를 벗어났습니다. 총 조인트 수: {len(joint_channels)}")
    
    joint_start_index = sum(joint_channels[:joint_index])
    joint_num_channels = joint_channels[joint_index]
    
    # 프레임 범위 검증
    if source_frame < 0 or source_frame >= num_frames:
        raise ValueError(f"소스 프레임 {source_frame}이 범위를 벗어났습니다. 유효 범위: 0 ~ {num_frames-1}")
    if start_frame < 0 or end_frame >= num_frames or start_frame > end_frame:
        raise ValueError(f"대상 프레임 범위가 잘못되었습니다. 유효 범위: 0 ~ {num_frames-1}")
    
    # 소스 프레임에서 조인트 값 추출
    source_line_idx = frames_index + source_frame
    if source_line_idx >= len(lines) or not lines[source_line_idx].strip():
        raise ValueError(f"소스 프레임 {source_frame}의 데이터를 찾을 수 없습니다")
    
    source_data = lines[source_line_idx].strip().split()
    if len(source_data) < joint_start_index + joint_num_channels:
        raise ValueError(f"소스 프레임 {source_frame}의 데이터가 부족합니다")
    
    # 복사할 값들 추출
    source_values = []
    for i in range(joint_num_channels):
        source_values.append(float(source_data[joint_start_index + i]))
    
    print(f"조인트 {joint_index} ({joint_names[joint_index]}):")
    print(f"  - 소스 프레임: {source_frame}")
    print(f"  - 복사할 값: {source_values}")
    print(f"  - 대상 프레임 범위: {start_frame} ~ {end_frame}")
    
    # 각 대상 프레임에 값 복사
    modified_frames = 0
    for frame_idx in range(num_frames):
        if start_frame <= frame_idx <= end_frame:
            line_idx = frames_index + frame_idx
            if line_idx >= len(lines) or not lines[line_idx].strip():
                continue
            
            # 들여쓰기 보존
            indent = lines[line_idx][:len(lines[line_idx]) - len(lines[line_idx].lstrip())]
            data = lines[line_idx].strip().split()
            
            if len(data) < joint_start_index + joint_num_channels:
                print(f"경고: 프레임 {frame_idx}의 데이터가 부족합니다")
                continue
            
            # 지정된 조인트의 값들을 소스에서 복사한 값으로 교체
            print(f"프레임 {frame_idx}의 조인트 {joint_index} ({joint_names[joint_index]}) 채널 {joint_start_index}~{joint_start_index + joint_num_channels - 1}: {data[joint_start_index:joint_start_index + joint_num_channels]} -> {source_values}")
            for i, source_value in enumerate(source_values):
                data[joint_start_index + i] = str(source_value)
            
            # 수정된 라인으로 교체
            lines[line_idx] = indent + " ".join(data) + "\n"
            modified_frames += 1
    
    # 수정된 BVH 파일 저장
    with open(output_file, 'w') as f:
        f.writelines(lines)
    
    print(f"성공적으로 {modified_frames}개 프레임이 수정되어 {output_file}에 저장되었습니다")


# 사용 예시
import shutil
if __name__ == "__main__":
    # BVH 파일 구조 분석
    input_file  = "./motions/SMPL/IAM.bvh"
    output_file = '.' + input_file.split('.')[1] + "_edited.bvh"
    shutil.copyfile(input_file, output_file) 

    # index 
    joint_index =[19, 20,  15,  15,  19,  19,  19,  19,  15,  15,  19]
    source_frame=[66, 99,  124, 142, 231, 234, 373, 395, 395, 419, 233]
    start_frame =[67, 100, 125, 143, 232, 235, 374, 396, 396, 420, 234]
    end_frame   =[73, 107, 137, 149, 233, 236, 378, 398, 400, 422, 236]
    # joint_index =[19,  19,  19,  15]
    # source_frame=[338, 152, 306, 346]
    # start_frame =[339, 147, 307, 347]
    # end_frame   =[370, 151, 310, 357]
    
    # analyiss bvh_structure
    joint_info = analyze_bvh_structure(input_file)
    
    # 특정 조인트의 특정 프레임 값 copy
    for i in range(len(joint_index)):
        copy_joint_values(
            input_file=output_file,
            output_file=output_file,
            joint_index=joint_index[i],
            source_frame=source_frame[i],
            start_frame =start_frame[i],
            end_frame=end_frame[i]
        )

    # 특정 조인트의 특정 프레임 값 수정
    # modify_joint_values(
    #     input_file=input_file,
    #     output_file=output_file, 
    #     joint_index=15,
    #     start_frame=127,
    #     end_frame=131,
    #     new_values=[-73.382, 8.01, 35.105] # [-73.382, 28.669, 76.008]
    # )