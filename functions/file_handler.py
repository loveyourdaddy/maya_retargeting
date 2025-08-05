import maya.cmds as cmds
import os
import maya.cmds as cmds
import maya.mel as mel
from functions.bvh_parsing import import_bvh


class FileHandler:
    """파일 가져오기 및 내보내기를 담당하는 클래스"""
    
    @staticmethod
    def import_motion_file(file_path, scale=1.0):
        """모션 파일(FBX 또는 BVH) 가져오기"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.fbx':
            mel.eval('FBXImport -f"{}"'.format(file_path))
            return True
        elif file_ext == '.bvh':
            return import_bvh(file_path, scale=scale)
        else:
            raise ValueError(f"지원되지 않는 파일 형식: {file_ext}")
    
    @staticmethod
    def import_texture(fbm_folder):
        """텍스처 파일 가져오기"""
        file_nodes = cmds.ls(type="file")
        imported_count = 0
        
        for node in file_nodes:
            new_path = os.path.join(fbm_folder, node)
            
            if os.path.exists(new_path):
                cmds.setAttr(node + ".fileTextureName", new_path, type="string")
                imported_count += 1
            else:
                print(f">>No texture: {new_path}")
                
        return imported_count
    
    @staticmethod
    def export(args, target_char, target_motion):
        """리타겟팅된 결과 내보내기"""
        # 출력 파일 경로 형성
        output_dir = f"./output/{target_char}"
        os.makedirs(output_dir, exist_ok=True)
        
        # 소스 모션 이름 추출
        motion_name = os.path.basename(args.sourceMotion).split('.')[0]
        output_file = f"{output_dir}/{motion_name}.fbx"
        
        # FBX 내보내기 옵션 설정
        cmds.FBXResetExport()
        mel.eval('FBXExportSmoothingGroups -v true')
        mel.eval('FBXExportEmbeddedTextures -v true')
        # mel.eval('FBXExportBakeComplexAnimation -v true')
        # mel.eval('FBXExportSkins -v true')
        # mel.eval('FBXExportShapes -v true')
        
        cmds.select(all=True)
        mel.eval('FBXExport -f "{}" -s'.format(output_file))
        
        print(f">> 리타겟팅된 파일 내보내기 완료: {output_file}")
        return output_file