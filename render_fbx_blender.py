# blender -b -P render_fbx.py -- "./output/Adori/1-8_Waacking_Twirl_RT0702.fbx" "/Users/inseo/2024_KAI_Retargeting/"
# blender -b -P render_fbx.py -- "./test_results/20250107_122504/Adori_qc/Adori2.1/Confident_004_RT0830.fbx" "/Users/inseo/2024_KAI_Retargeting/test_videos/20250107_122504/Adori_qc/Adori2.1"

import bpy
import math
import os
import sys
import time
from mathutils import Vector
import time 
import pdb; 

def clean_scene():
    """새로운 씬을 생성합니다."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 기본 큐브, 라이트, 카메라 삭제
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for light in bpy.data.lights:
        bpy.data.lights.remove(light)
    for cam in bpy.data.cameras:
        bpy.data.cameras.remove(cam)

def setup_lighting():
    """조명을 설정합니다."""
    # 키 라이트 (주 조명)
    key_light = bpy.data.lights.new(name='Key_Light', type='SUN')
    key_light.energy = 5.0
    key_light.color = (1, 1, 1)
    key_light_obj = bpy.data.objects.new(name='Key_Light', object_data=key_light)
    bpy.context.scene.collection.objects.link(key_light_obj)
    key_light_obj.location = (5, 5, 10)
    key_light_obj.rotation_euler = (-0.785, 0.785, 0)

    # 필 라이트 (보조 조명)
    fill_light = bpy.data.lights.new(name='Fill_Light', type='SUN')
    fill_light.energy = 2.0
    fill_light.color = (0.8, 0.8, 1)
    fill_light_obj = bpy.data.objects.new(name='Fill_Light', object_data=fill_light)
    bpy.context.scene.collection.objects.link(fill_light_obj)
    fill_light_obj.location = (-5, 5, 8)
    fill_light_obj.rotation_euler = (-0.523, -0.785, 0)

    # 백 라이트 (뒷면 조명)
    back_light = bpy.data.lights.new(name='Back_Light', type='SUN')
    back_light.energy = 3.0
    back_light_obj = bpy.data.objects.new(name='Back_Light', object_data=back_light)
    bpy.context.scene.collection.objects.link(back_light_obj)
    back_light_obj.location = (0, -5, 8)
    back_light_obj.rotation_euler = (-0.785, 0, 0)

def calculate_camera_position(obj):
    """객체의 바운딩 박스를 기반으로 카메라 위치를 계산합니다."""
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    bbox_min = Vector(map(min, zip(*bbox_corners)))
    bbox_max = Vector(map(max, zip(*bbox_corners)))
    
    # 객체의 크기와 중심점 계산
    dimensions = bbox_max - bbox_min
    center = (bbox_max + bbox_min) / 2
    
    # 카메라 거리 계산
    max_dim = max(dimensions.x, dimensions.y, dimensions.z)
    camera_distance = max_dim * 2.5
    
    # 카메라 위치 계산 (15도 위에서 바라보기)
    angle = math.radians(15)
    camera_pos = center + Vector((0, -camera_distance * math.cos(angle), camera_distance * math.sin(angle)))
    
    return camera_pos, center

def setup_camera():
    """카메라를 설정합니다."""
    cam_data = bpy.data.cameras.new(name='RenderCam')
    cam_obj = bpy.data.objects.new('RenderCam', cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    
    # 렌더링 카메라로 설정
    bpy.context.scene.camera = cam_obj
    
    # 카메라 렌즈 설정
    cam_data.lens = 35
    cam_data.sensor_width = 36
    
    return cam_obj

def import_fbx(fbx_path):
    """FBX 파일을 임포트합니다."""
    try:
        bpy.ops.import_scene.fbx(filepath=fbx_path)
        
        # 임포트된 객체들 찾기
        imported_objects = []
        for obj in bpy.context.scene.objects:
            if obj.type in {'MESH', 'ARMATURE'}:
                imported_objects.append(obj)
        
        if not imported_objects:
            raise Exception("No valid objects found in the imported FBX")
            
        # 첫 번째 메시 또는 아마추어를 기준으로 카메라 위치 계산
        main_obj = imported_objects[0]
        camera_pos, look_at = calculate_camera_position(main_obj)
        
        # 카메라 설정 업데이트
        cam = bpy.context.scene.camera
        cam.location = camera_pos
        
        # 카메라가 객체를 바라보도록 설정
        direction = look_at - camera_pos
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam.rotation_euler = rot_quat.to_euler()
        
        return main_obj
        
    except Exception as e:
        print(f"Error importing FBX: {str(e)}")
        raise

def setup_render_settings():
    """렌더링 설정을 구성합니다."""
    # 프레임 완료 핸들러 등록
    # import pdb; pdb.set_trace()
    bpy.app.handlers.render_complete.clear()
    # bpy.app.handlers.render_complete.append(frame_complete_callback)
    
    # 블렌더 로그 출력 끄기
    bpy.context.preferences.view.show_splash = False
    bpy.context.preferences.view.show_tooltips = False
    bpy.context.preferences.view.show_tooltips_python = False
    
    # 렌더링 중 콘솔 출력 제한
    # bpy.context.scene.render.use_progress = False
    # bpy.context.scene.render.use_stats = False

    scene = bpy.context.scene
    
    # 렌더러 설정
    scene.render.engine = 'BLENDER_EEVEE_NEXT'  # 빠른 렌더링을 위해 EEVEE 사용
    
    # 해상도 설정
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    # 출력 설정
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4' # MPEG4
    scene.render.ffmpeg.codec = 'H264'
    # scene.render.ffmpeg.constant_rate_factor = '23'
    scene.render.ffmpeg.ffmpeg_preset = 'REALTIME' # BEST', 'GOOD', 'REALTIME' TODO
    
    # 프레임 레이트 설정
    scene.render.fps = 30
    
    # EEVEE 특정 설정
    scene.eevee.use_soft_shadows = True
    scene.eevee.use_bloom = True
    scene.eevee.use_ssr = True
    scene.eevee.use_ssr_refraction = True

def setup_animation():
    """애니메이션 프레임 범위를 설정합니다."""
    # 모든 액션에서 프레임 범위 찾기
    start_frame = float('inf')
    end_frame = float('-inf')
    
    # pdb.set_trace()
    for action in bpy.data.actions:
        if action.frame_range[0] < start_frame:
            start_frame = action.frame_range[0]
        if action.frame_range[1] > end_frame:
            end_frame = action.frame_range[1]
    
    # pdb.set_trace()
    if start_frame == float('inf'):
        start_frame = 1
    if end_frame == float('-inf'):
        end_frame = 250
    end_frame = 2
    
    # 프레임 범위 설정
    bpy.context.scene.frame_start = int(start_frame)
    bpy.context.scene.frame_end = int(end_frame)
    
    return int(start_frame), int(end_frame)

def render_animation(output_dir, source_fbx_path):
    """애니메이션을 렌더링합니다."""
    motion_name = os.path.splitext(os.path.basename(source_fbx_path))[0]
    output_path = os.path.join(output_dir, f"{motion_name}.mp4")
    
    # 출력 경로 설정
    bpy.context.scene.render.filepath = output_path
    
    # 렌더링 실행
    bpy.ops.render.render(animation=True)
    
    return output_path

def main():
    if len(sys.argv) < 5:
        print("Usage: blender -b -P render_fbx.py -- <input_fbx> <output_dir>")
        sys.exit(1)
    
    # Blender의 기본 인자 이후의 인자들을 가져옴
    # pdb.set_trace()
    args = sys.argv[sys.argv.index("--") + 1:]
    input_fbx = args[0]
    output_dir = args[1]
    
    try:
        time0 = time.time()
        # 씬 초기화
        clean_scene()
        
        # pdb.set_trace()
        # 렌더링 설정
        setup_lighting()
        setup_camera()
        setup_render_settings()
        
        # FBX 임포트 및 설정
        import_fbx(input_fbx)
        start_frame, end_frame = setup_animation()
        print(f"Frame: {start_frame} ~ {end_frame}")
        # pdb.set_trace()
        
        # 렌더링 실행
        output_path = render_animation(output_dir, input_fbx)
        print(f"Successfully created MP4: {output_path}")

        time1 = time.time()
        print(f"Time: {int((time1 - time0) // 60)}m {int(time1 - time0) % 60}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()