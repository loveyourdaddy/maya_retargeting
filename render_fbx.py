# mayapy render/render_fbx.py "./output/Adori/1-8_Waacking_Twirl_RT0702.fbx" "/Users/inseo/2024_KAI_Retargeting/render/"  
import maya.cmds as cmds
# import logging
import maya.mel as mel
import maya.standalone
import os
import sys
# import maya.OpenMaya as OpenMaya
import time 
import math

def setup_scene():
    # 새로운 씬 생성
    cmds.file(new=True, force=True)
    
    key_light_transform = cmds.directionalLight(name='keyLight')
    cmds.move(200, 200, 200, key_light_transform)
    cmds.rotate(-45, 45, 0, key_light_transform)
    cmds.setAttr(f"{key_light_transform}.intensity", 2.0)
    cmds.setAttr(f"{key_light_transform}.color", 1, 1, 1, type="double3")
    
    # 필 라이트 (반대쪽에서 그림자를 밝혀주는 보조 조명)
    fill_light_transform = cmds.directionalLight(name='fillLight')
    cmds.move(-150, 150, 150, fill_light_transform)
    cmds.rotate(-30, -45, 0, fill_light_transform)
    cmds.setAttr(f"{fill_light_transform}.intensity", 1.0)
    cmds.setAttr(f"{fill_light_transform}.color", 0.8, 0.8, 1, type="double3")
    
    # 백 라이트 (뒤에서 비추어 입체감을 주는 조명)
    back_light_transform = cmds.directionalLight(name='backLight')
    cmds.move(0, 200, -200, back_light_transform)
    cmds.rotate(-45, 0, 0, back_light_transform)
    cmds.setAttr(f"{back_light_transform}.intensity", 1.0)
    
    # 앰비언트 라이트 (전체적인 기본 조명)
    ambient_light_transform = cmds.ambientLight(name='ambientLight')
    cmds.setAttr(f"{ambient_light_transform}.intensity", 0.2)
    
def calculate_camera_position(bbox):
    """캐릭터의 바운딩 박스를 기반으로 카메라 위치 계산"""
    min_x, min_y, min_z, max_x, max_y, max_z = bbox
    
    # 캐릭터의 높이와 너비 계산
    height = max_y - min_y
    width = max_x - min_x
    depth = max_z - min_z
    
    # 캐릭터의 중심점 계산
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    
    # 기본 카메라 거리 계산
    base_distance = max(height * 1.5, width * 2.5)

    # 카메라 회전각 계산 (라디안)
    rot_x = math.radians(-15)  # -15도
    rot_y = math.radians(0)    # 0도
    
    # 회전 행렬 적용하여 카메라 위치 계산
    # 먼저 카메라를 Z축 방향으로 이동
    cam_x = 0
    cam_y = 0
    cam_z = base_distance
    
    # Y축 회전 (rot_y)
    cos_y = math.cos(rot_y)
    sin_y = math.sin(rot_y)
    temp_x = cam_x * cos_y + cam_z * sin_y
    temp_z = -cam_x * sin_y + cam_z * cos_y
    cam_x = temp_x
    cam_z = temp_z
    
    # X축 회전 (rot_x)
    cos_x = math.cos(rot_x)
    sin_x = math.sin(rot_x)
    temp_y = cam_y * cos_x - cam_z * sin_x
    temp_z = cam_y * sin_x + cam_z * cos_x
    cam_y = temp_y
    cam_z = temp_z
    
    # 캐릭터의 중심점을 기준으로 카메라 위치 조정
    cam_x += center_x
    cam_y += center_y + (height * 0.1)  # 캐릭터 높이의 10% 위에서 촬영
    cam_z += center_z
    
    return {
        'position': [cam_x, cam_y, cam_z],
        'target': [center_x, center_y, center_z],
        'rotation': [math.degrees(rot_x), math.degrees(rot_y), 0],
        'film_fit': 'vertical' if height > width else 'horizontal'
    }

def setup_camera(bbox):
    # 카메라 생성 및 설정
    camera_transform, camera_shape = cmds.camera(name='renderCam')

    # 카메라 설정 TODO 
    cam_settings = calculate_camera_position(bbox)
    
    cmds.setAttr(f"{camera_transform}.translateX", cam_settings['position'][0])
    cmds.setAttr(f"{camera_transform}.translateY", cam_settings['position'][1])
    cmds.setAttr(f"{camera_transform}.translateZ", cam_settings['position'][2])
    
    # 먼저 회전 설정
    cmds.setAttr(f"{camera_transform}.rotateX", cam_settings['rotation'][0])
    cmds.setAttr(f"{camera_transform}.rotateY", cam_settings['rotation'][1])
    cmds.setAttr(f"{camera_transform}.rotateZ", cam_settings['rotation'][2])
    
    # 그 다음 위치 설정
    cmds.setAttr(f"{camera_transform}.translateX", cam_settings['position'][0])
    cmds.setAttr(f"{camera_transform}.translateY", cam_settings['position'][1])
    cmds.setAttr(f"{camera_transform}.translateZ", cam_settings['position'][2])
    
    # 카메라 설정
    cmds.setAttr(f"{camera_shape}.focalLength", 35)
    cmds.setAttr(f"{camera_shape}.verticalFilmAperture", 1.417)
    cmds.setAttr(f"{camera_shape}.filmFit", 1 if cam_settings['film_fit'] == 'horizontal' else 2)
    
    # 렌더링 카메라로 설정
    cmds.setAttr(f"{camera_shape}.renderable", 1)
    
    for cam in cmds.ls(type='camera'):
        if cam != camera_shape:
            cmds.setAttr(f"{cam}.renderable", 0)
    
    return camera_shape

def import_fbx(fbx_path):
    try:
        # FBX 플러그인 로드
        if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            cmds.loadPlugin("fbxmaya")
        
        # MEL 명령어로 FBX 임포트
        mel_cmd = f'FBXImport -file "{fbx_path}";'
        mel.eval(mel_cmd)
        
        # 모든 조인트 선택
        joints = cmds.ls(type='joint')
        if joints:
            # 캐릭터의 루트 조인트를 찾아서 위치 조정
            root_joint = joints[0]
            for joint in joints:
                if cmds.listRelatives(joint, parent=True) is None:
                    root_joint = joint
                    break
                    
            # 캐릭터를 원점으로 이동
            cmds.select(root_joint)
            cmds.move(0, 0, 0, root_joint, absolute=True)

        meshes = cmds.ls(type='mesh')
        if not meshes:
            raise Exception("No meshes found in the imported FBX")
        bbox = None
        for mesh in meshes:
            mesh_bbox = cmds.exactWorldBoundingBox(mesh)
            if bbox is None:
                bbox = list(mesh_bbox)
            else:
                bbox = [
                    min(bbox[0], mesh_bbox[0]),
                    min(bbox[1], mesh_bbox[1]),
                    min(bbox[2], mesh_bbox[2]),
                    max(bbox[3], mesh_bbox[3]),
                    max(bbox[4], mesh_bbox[4]),
                    max(bbox[5], mesh_bbox[5])
                ]
        
        return bbox
        
    except Exception as e:
        print(f"Error importing FBX: {str(e)}")
        raise

def setup_playback():
    # 애니메이션 시작/끝 프레임 가져오기
    start_time = int(cmds.playbackOptions(query=True, minTime=True))
    end_time = int(cmds.playbackOptions(query=True, maxTime=True))
    
    # 프레임 범위가 0이면 기본값 설정
    if start_time == end_time:
        # FBX의 애니메이션 노드에서 시작/끝 프레임 가져오기
        anim_curves = cmds.ls(type='animCurve')
        if anim_curves:
            all_times = []
            for curve in anim_curves:
                times = cmds.keyframe(curve, query=True)
                if times:
                    all_times.extend(times)
            if all_times:
                start_time = int(min(all_times))
                end_time = int(max(all_times))
    
    print(f">>> Animation frame range: from {start_time} to {end_time}, {start_time} - {end_time}")
    
    # 프레임 레이트 설정 (30fps)
    cmds.currentUnit(time='ntsc')
    
    # 플레이백 범위 설정
    cmds.playbackOptions(minTime=start_time)
    cmds.playbackOptions(maxTime=end_time)
    
    return start_time, end_time


def setup_software_renderer():
    # 렌더러를 Maya Software로 설정
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "mayaSoftware", type="string")
    
    # 이미지 포맷 설정
    cmds.setAttr("defaultRenderGlobals.imageFormat", 8)  # JPEG
    cmds.setAttr("defaultRenderGlobals.imfkey", "jpg", type="string")
    
    # 해상도 설정
    cmds.setAttr("defaultResolution.width", 1920)
    cmds.setAttr("defaultResolution.height", 1080)
    cmds.setAttr("defaultResolution.deviceAspectRatio", 1.777777)
        
    # 렌더링 품질 설정
    cmds.setAttr("defaultRenderQuality.shadingSamples", 4)  # 증가된 샘플링
    cmds.setAttr("defaultRenderQuality.maxShadingSamples", 16)
    
    # 그림자 설정
    cmds.setAttr("defaultRenderGlobals.enableDefaultLight", 0)  # 기본 조명 비활성화
    
    # 애니메이션 설정
    cmds.setAttr("defaultRenderGlobals.animation", 1)
    cmds.setAttr("defaultRenderGlobals.putFrameBeforeExt", 1)
    cmds.setAttr("defaultRenderGlobals.periodInExt", 1)
    cmds.setAttr("defaultRenderGlobals.outFormatControl", 0)
    cmds.setAttr("defaultRenderGlobals.extensionPadding", 4)

def render_sequence(render_camera, output_dir, start_time, end_time, source_fbx_path=None):
    # input_fbx의 파일명을 추출하여 사용
    if source_fbx_path is None:
        motion_name = "animation"
    else:
        motion_name = os.path.splitext(os.path.basename(source_fbx_path))[0]
    
    image_dir = os.path.join(output_dir, f"{motion_name}_frames")
    os.makedirs(image_dir, exist_ok=True)
    
    # 렌더링 설정
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", f"{image_dir}/{motion_name}", type="string")
    cmds.setAttr("defaultRenderGlobals.startFrame", start_time)
    cmds.setAttr("defaultRenderGlobals.endFrame", end_time)
    
    # 프레임 범위 출력
    print(f"Rendering frames from {start_time} to {end_time}")
    
    # 렌더링 실행
    for frame in range(start_time, end_time + 1):
        print(f"Rendering frame {frame}...")
        cmds.currentTime(frame)
        try:
            # 현재 프레임 번호 설정
            cmds.setAttr("defaultRenderGlobals.startFrame", frame)
            cmds.setAttr("defaultRenderGlobals.endFrame", frame)
            
            # 카메라 shape 노드로 렌더링
            cmds.render(render_camera, x=1920, y=1080, b=True)
        except Exception as e:
            raise
    
    # 이미지 시퀀스를 MP4로 변환
    image_pattern = os.path.join(image_dir, f"{motion_name}.*.jpg")
    output_mp4 = os.path.join(output_dir, f"{motion_name}.mp4")
    
    # ffmpeg를 사용하여 이미지 시퀀스를 MP4로 변환
    os.system(f'ffmpeg -y -hide_banner -loglevel panic -framerate 30 '
             f'-pattern_type glob -i "{image_pattern}" '
             f'-c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p "{output_mp4}" 2>/dev/null')
    
    os.system(f'rm -rf "{image_dir}"')
    
    return output_mp4

def main():
    # Maya standalone 모드 초기화
    maya.standalone.initialize()
    
    if len(sys.argv) != 3:
        print("Usage: mayapy render_fbx_maya.py <input_fbx> <output_dir>")
        sys.exit(1)
    
    input_fbx = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        setup_scene()
        bbox = import_fbx(input_fbx)
        render_camera = setup_camera(bbox)
        start_time, end_time = setup_playback()
        setup_software_renderer()
        time.sleep(1)
        output_mp4 = render_sequence(render_camera, output_dir, start_time, end_time, input_fbx)

        print(f"Successfully created MP4: {output_mp4}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    finally:
        # Maya 종료
        maya.standalone.uninitialize()

if __name__ == "__main__":
    main()