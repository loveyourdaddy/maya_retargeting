
import logging
import datetime
import os 


def setup_logger(sourceChar, sourceMotion, targetChar):
    # 로그 디렉토리 생성
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 타임스탬프를 포함한 로그 파일 이름 생성
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # sourceChar, sourceMotion, targetChar
    sourceMotion_name = os.path.basename(sourceMotion).split('.')[0]
    log_filename = f"{log_dir}/{timestamp}_{sourceChar}_{sourceMotion_name}_2_{targetChar}.log"
    print(f"로그 파일: {log_filename}")
    
    # 로거 설정
    logger = logging.getLogger('retargeting')
    logger.setLevel(logging.DEBUG)
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    
    # 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    
    return logger