# mayapy render/render_fbx.py "./output/Adori/1-8_Waacking_Twirl_RT0702.fbx" "/Users/inseo/2024_KAI_Retargeting/render/"
import maya.cmds as cmds
import maya.mel as mel
import maya.standalone
import os
import sys
import math

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
    
    # 카메라 위치 계산
    cam_height = center_y + (height * 0.1)  # 캐릭터 높이의 10% 위에서 촬영
    cam_distance = max(height * 1.5, width * 2.5)  # 캐릭터 높이의 1.5배 또는 너비의 2.5배 중 큰 값
    
    return {
        'position': [center_x, cam_height, center_z + cam_distance],
        'target': [center_x, center_y, center_z],
        'fov': 40,
        'film_fit': 'vertical' if height > width else 'horizontal'
    }
    
def setup_scene():
    # 새로운 씬 생성
    cmds.file(new=True, force=True)
    
    # 조명 설정
    key_light = cmds.directionalLight(name='keyLight', position=[100, 100, 100])
    cmds.setAttr(f"{key_light}.intensity", 1.5)
    
    fill_light = cmds.directionalLight(name='fillLight', position=[-50, 100, 50])
    cmds.setAttr(f"{fill_light}.intensity", 0.8)
    
    # 카메라는 나중에 설정
    return None

def setup_camera(bbox):
    camera_transform, camera_shape = cmds.camera(name='renderCam')
    
    cam_settings = calculate_camera_position(bbox)
    
    cmds.setAttr(f"{camera_transform}.translateX", cam_settings['position'][0])
    cmds.setAttr(f"{camera_transform}.translateY", cam_settings['position'][1])
    cmds.setAttr(f"{camera_transform}.translateZ", cam_settings['position'][2])
    
    # 카메라가 캐릭터의 중심을 바라보도록 회전각 계산
    target = cam_settings['target']
    pos = cam_settings['position']
    
    # 카메라의 방향을 타겟으로 향하게 설정
    direction = [
        target[0] - pos[0],
        target[1] - pos[1],
        target[2] - pos[2]
    ]
    
    # 회전각 계산 (라디안)
    rot_x = -math.atan2(direction[1], math.sqrt(direction[0]**2 + direction[2]**2))
    rot_y = math.atan2(direction[0], direction[2])
    
    # 라디안을 도로 변환하여 설정
    cmds.setAttr(f"{camera_transform}.rotateX", math.degrees(rot_x))
    cmds.setAttr(f"{camera_transform}.rotateY", math.degrees(rot_y))
    cmds.setAttr(f"{camera_transform}.rotateZ", 0)
    
    cmds.setAttr(f"{camera_shape}.focalLength", 35)
    cmds.setAttr(f"{camera_shape}.verticalFilmAperture", 1.417)
    cmds.setAttr(f"{camera_shape}.filmFit", 1 if cam_settings['film_fit'] == 'horizontal' else 2)
    
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
        
        # 모든 메쉬의 바운딩 박스 계산
        meshes = cmds.ls(type='mesh')
        if not meshes:
            raise Exception("No meshes found in the imported FBX")
        
        # 전체 바운딩 박스 계산
        bbox = None
        for mesh in meshes:
            mesh_bbox = cmds.exactWorldBoundingBox(mesh)
            if bbox is None:
                bbox = list(mesh_bbox)
            else:
                bbox = [
                    min(bbox[0], mesh_bbox[0]),  # min_x
                    min(bbox[1], mesh_bbox[1]),  # min_y
                    min(bbox[2], mesh_bbox[2]),  # min_z
                    max(bbox[3], mesh_bbox[3]),  # max_x
                    max(bbox[4], mesh_bbox[4]),  # max_y
                    max(bbox[5], mesh_bbox[5])   # max_z
                ]
        
        return bbox
        
    except Exception as e:
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
    
    print(f"Animation frame range: {start_time} - {end_time}")
    
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
    cmds.setAttr("defaultRenderQuality.shadingSamples", 2)
    cmds.setAttr("defaultRenderQuality.maxShadingSamples", 8)
    
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
            print(f"Error rendering frame {frame}: {str(e)}")
            raise
    
    # 이미지 시퀀스를 MP4로 변환
    image_pattern = os.path.join(image_dir, f"{motion_name}.*.jpg")
    output_mp4 = os.path.join(output_dir, f"{motion_name}.mp4")
    
    # ffmpeg를 사용하여 이미지 시퀀스를 MP4로 변환
    os.system(f'ffmpeg -framerate 30 -pattern_type glob -i "{image_pattern}" '
             f'-c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p "{output_mp4}"')
    
    # 임시 이미지 파일들 정리
    os.system(f'rm -rf "{image_dir}"')
    
    return output_mp4

def main():
    # Maya standalone 모드 초기화
    maya.standalone.initialize()
    
    if len(sys.argv) != 3:
        print("Usage: mayapy render_fbx_maya.py <input_fbx> <output_dir>")
        sys.exit(1)
    
    input_fbx = sys.argv[1]
    output_dir = sys.argv[2] # "/Users/inseo/2024_KAI_Retargeting/render/"
    
    try:
        # 씬 설정 및 카메라 생성
        # 기본 씬 설정
        setup_scene()
        
        # FBX 임포트 및 바운딩 박스 계산
        bbox = import_fbx(input_fbx)

        # 바운딩 박스 기반으로 카메라 설정
        render_camera = setup_camera(bbox)
        
        # 플레이백 설정
        start_time, end_time = setup_playback()
        
        # Maya Software 렌더러 설정
        setup_software_renderer()
        
        # 시퀀스 렌더링
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