# mayapy render/render_fbx.py "./output/Adori/1-8_Waacking_Twirl_RT0702.fbx" "/Users/inseo/2024_KAI_Retargeting/render/"  
import maya.cmds as cmds
import logging
import maya.mel as mel
import maya.standalone
import os
import sys
import maya.OpenMaya as OpenMaya
import time 

# Maya 로그 레벨 설정
# logging.getLogger('maya').setLevel(logging.CRITICAL)

def silence_output():
    """Maya의 출력을 제거하는 함수"""
    # OpenMaya.MGlobal.executeCommand("scriptEditorInfo -suppressResults true -suppressErrors true -suppressWarnings true -suppressInfo true;", False, False)
    # OpenMaya.MGlobal.executeCommand("scriptEditorInfo -suppressStackTrace true;", False, False)
    # # 렌더링 진행상황 메시지 제거
    # OpenMaya.MGlobal.executeCommand("scriptEditorInfo -suppressResolutionInformation true;", False, False)
    # 모든 Maya 출력 제거
    mel.eval('scriptEditorInfo -suppressInfo true;')
    mel.eval('scriptEditorInfo -suppressWarnings true;')
    mel.eval('scriptEditorInfo -suppressErrors true;')
    mel.eval('scriptEditorInfo -suppressResults true;')
    
    # 렌더링 관련 출력 제거
    mel.eval('putenv "MAYA_SUPPRESS_RENDERING_PERFORMANCE_STATS" "1";')
    mel.eval('putenv "MAYA_SUPPRESS_RENDERING_STATS" "1";')
    mel.eval('putenv "MAYA_DISABLE_PERFORMANCE_STATS" "1";')
    
    # 추가 렌더 설정
    # cmds.setAttr("defaultRenderGlobals.printGeometryStats", 0)
    # cmds.setAttr("defaultRenderGlobals.printResourceStats", 0)
    # cmds.setAttr("defaultRenderGlobals.printRenderingStats", 0)
    

def setup_scene():
    # 새로운 씬 생성
    cmds.file(new=True, force=True)
    
    # 카메라 생성 및 설정
    camera_transform, camera_shape = cmds.camera(name='renderCam')
    print(f"Created camera: transform={camera_transform}, shape={camera_shape}")
    
    cmds.setAttr(f"{camera_transform}.translateX", 0)
    cmds.setAttr(f"{camera_transform}.translateY", 100)
    cmds.setAttr(f"{camera_transform}.translateZ", 400)
    cmds.setAttr(f"{camera_transform}.rotateX", -15)
    cmds.setAttr(f"{camera_transform}.rotateY", 0)
    cmds.setAttr(f"{camera_transform}.rotateZ", 0)
    
    # 렌더 카메라로 설정
    cmds.setAttr(f"{camera_shape}.renderable", 1)
    
    # 다른 카메라들의 renderable 속성을 끔
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

    # 출력 제거 설정
    silence_output()
    
    if len(sys.argv) != 3:
        print("Usage: mayapy render_fbx_maya.py <input_fbx> <output_dir>")
        sys.exit(1)
    
    input_fbx = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        # 씬 설정 및 카메라 생성
        render_camera = setup_scene()
        print(f"Using render camera: {render_camera}")
        
        # FBX 임포트
        import_fbx(input_fbx)
        
        # 플레이백 설정
        start_time, end_time = setup_playback()
        
        # Maya Software 렌더러 설정
        setup_software_renderer()
        time.sleep(1)
        
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