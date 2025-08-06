"""
Usage: 
    python run_retargeting.py --sourceChar <source_character_path> --sourceMotion <source_motion_path> --targetChar <target_character_path>

source motion as
1.  fbx
    mayapy run_retargeting.py --sourceChar "./models/Asooni/Asooni.fbx" --sourceMotion "./motions/Asooni/Supershy.fbx" --targetChar "./models/SMPL/SMPL.fbx"
2. bvh
    mayapy run_retargeting.py --sourceChar "./models/Asooni/Asooni.fbx" --sourceMotion "./motions/Asooni/Supershy.bvh" --targetChar "./models/SMPL/SMPL.fbx"
"""

import maya.cmds as cmds
import maya.standalone
from functions.parser import *
from functions.character import *
from functions.motion import *
from functions.maya import *
from functions.bvh_parsing import *
from functions.file_handler import FileHandler
from functions.log import *
from functions.retargeting_processor import RetargetingProcessor
from make_Tpose import make_Tpose
import time


class RetargetingPipeline:
    """전체 리타겟팅 파이프라인을 관리하는 클래스"""
    
    def __init__(self):
        self.args = get_args()
        self.source_char = None
        self.target_char = None
        self.file_handler = FileHandler()
        self.logger = None
        self.start_time = None
    
    def initialize(self):
        """Maya 초기화 및 플러그인 로드"""
        self.start_time = time.time()
        maya.standalone.initialize(name='python')
        
        # FBX 플러그인 로드
        if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
            cmds.loadPlugin('fbxmaya')
    
    def setup_characters(self):
        """캐릭터 설정"""
        # 대상 캐릭터 설정
        target_char_name = get_name(self.args.targetChar)
        target_motion_name = get_name(self.args.sourceMotion)
        
        # 소스 캐릭터 설정
        source_motion = self.args.sourceMotion
        
        if self.args.sourceChar != '':
            source_char_name = self.args.sourceChar.split('/')[-2]
        else:
            source_char_name = source_motion.split('/')[-2]
        
        # 로거 설정
        self.logger = setup_logger(source_char_name, source_motion, target_char_name)
        self.logger.info(f"Source: ({source_char_name}, {source_motion}) -> Target: {target_char_name}")
        
        # 캐릭터 객체 생성
        self.source_char = Character(source_char_name) # TODO: check namespace of character
        self.target_char = Character(target_char_name, namespace="tgt")
        
        return source_char_name, target_char_name, source_motion
    
    def import_target_character(self):
        """대상 캐릭터 가져오기"""
        # FBX 가져오기 설정
        mel.eval('FBXImportSmoothingGroups -v true')
        mel.eval('FBXImport -f"{}"'.format(self.args.targetChar))
        
        # .fbm 폴더 경로
        path = f"./models/{self.target_char.name}/{self.target_char.name}"
        fbm_folder = path + ".fbm"
        
        # 텍스처 가져오기
        imported_count = self.file_handler.import_texture(fbm_folder)
        print(f">> {imported_count} 텍스처 로드됨")
        
        # 조인트 및 메쉬 정보 추출
        self.target_char.get_tgt_joints()
        self.target_char.get_meshes()
    
    def import_source_character(self, source_char_name, source_motion):
        """소스 캐릭터 가져오기"""
        sourceChar_path = f'./models/{source_char_name}/{source_char_name}.fbx'
        
        if os.path.exists(sourceChar_path):
            # 소스 캐릭터가 있으면 가져오기
            mel.eval('FBXImport -f"{}"'.format(sourceChar_path))
        elif os.path.exists(sourceChar_path) == False or self.args.sourceChar == '':
            # 소스 캐릭터가 없거나 소스 캐릭터가 입력으로 들어오지 않는 경우
            if os.path.exists(sourceChar_path) == False:
                print(">> 소스 캐릭터 없음")
            if self.args.sourceChar == '':
                print(">> 소스 캐릭터가 입력되지 않음")
            
            # 해당 경로의 T-포즈 가져오기
            file_format = source_motion.split('.')[-1]
            tpose_path = os.path.join(os.path.dirname(source_motion), 'Tpose.' + file_format)
            # T-포즈 생성 기능 구현 필요
        else:
            raise ValueError("소스 캐릭터가 없습니다")
        
        # 소스 메쉬 이름 변경
        self.source_char.get_meshes()
        
        # 조인트 정보 추출
        self.source_char.get_src_joints(self.target_char.joints)
        
        # 로케이터 정보 추출
        locators_list = cmds.ls(type='locator')
        src_locator_list = list(set(locators_list) - set(self.target_char.locator_list))
        
        if len(src_locator_list) != 0:
            # 올바른 로케이터 선택
            src_locator_list = sorted(src_locator_list, key=lambda x: len(cmds.listRelatives(x, children=True) or []), reverse=True)
            
            # 네임스페이스 'tgt'가 없는 소스 로케이터 선택
            src_locator_candidate = []
            for locator in src_locator_list:
                if locator.split(':')[0] != 'tgt':
                    src_locator_candidate.append(locator)
            
            # 가장 많은 자식을 가진 로케이터 선택
            if src_locator_candidate:
                # remove "shape"
                locator = src_locator_candidate[0]
                locator = locator.replace("Shape","")

                self.source_char.locator, self.source_char.locator_angle, \
                self.source_char.locator_scale, self.source_char.locator_pos = \
                    self.source_char._get_locator(locator)
    
    def import_source_motion(self, source_motion):
        """소스 모션 가져오기"""
        self.file_handler.import_motion_file(source_motion)
        
        # 소스 모션의 FPS 설정
        current_fps = mel.eval('currentTimeUnitToFPS')
        mel.eval(f'currentUnit "{current_fps}fps"')
        print("소스 fps:", current_fps)
    
    def export_result(self):
        """결과 내보내기"""
        output_file = self.file_handler.export(self.args, self.target_char.name, get_name(self.args.sourceMotion))
        return output_file
    
    def finalize(self):
        """Maya 종료 및 실행 시간 기록"""
        maya.standalone.uninitialize()
        
        # 종료 시간
        end_time = time.time()
        execution_time = end_time - self.start_time
        minutes = int(execution_time // 60)
        seconds = execution_time % 60
        
        print(f">> 실행 시간: {execution_time:.3f}, ({minutes}분 {seconds:.3f}초)")
        self.logger.info(f"실행 시간: {execution_time:.3f}, ({minutes}분 {seconds:.3f}초)")
    
    def run(self):
        """전체 리타겟팅 파이프라인 실행"""
        try:
            # 초기화
            self.initialize()
            
            # 캐릭터 설정
            source_char_name, target_char_name, source_motion = self.setup_characters()
            
            # 대상 캐릭터 가져오기
            self.import_target_character()
            
            # 소스 캐릭터 가져오기
            self.import_source_character(source_char_name, source_motion)
            
            # 리타겟팅 프로세서 생성
            self.processor = RetargetingProcessor(self.source_char, self.target_char)
            
            # 공통 스켈레톤 생성
            self.processor.get_common_skeleton()
            
            # 루트 관절 식별
            self.processor.identify_root_joints()

            # source와 target 사이의 height ratio
            self.processor.get_height_ratio()

            # 로케이터 회전 정제
            self.target_char.refine_locator_rotation()
            
            # 소스 모션 가져오기
            self.import_source_motion(source_motion)
            
            # 리타겟팅 수행
            self.processor.retarget()
            
            # 소스 정리
            self.processor.cleanup_source()
            
            # 타겟 객체 이름 변경
            self.processor.rename_target_objects(self.target_char.joints_origin)
            
            # 결과 내보내기
            output_file = self.export_result()
            print(f">> 리타겟팅 완료: {output_file}")
            
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            self.logger.error(f"오류 발생: {str(e)}", exc_info=True)
        finally:
            # 종료
            self.finalize()


def main():
    """메인 함수"""
    pipeline = RetargetingPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()