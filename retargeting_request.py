import requests
# import subprocess
import os
from functions.parser import *
import sys

class Mingle_API():
    def __init__(self, url='http://127.0.0.1:5000/'):
        self.base_url = url

    def call_retargeting_api(self, target_character, source_character, source_motion): 
        # retarget api 
        upload_url = os.path.join(self.base_url, "upload")
        files = {
            'file1': open(target_character, 'rb'),
            'file2': open(source_character, 'rb'),
            'file3': open(source_motion, 'rb')
        }
        response = requests.post(upload_url, files=files)
        print("Upload response:", response.json())

        # 처리 시간을 위한 지연
        import time
        time.sleep(5) # 5초 대기

        # download retargeted fbx
        download_url = os.path.join(self.base_url, 'download')
        download_response = requests.post(download_url)
        print("Download response:", download_response)
        print("Download response response:", download_response.json())
        print("Download response content:", download_response.content)
        print(" status_code:", download_response.status_code)


        if download_response.status_code == 200:
            # 파일 저장
            filename = download_response.headers.get('X-Filename')
            print("filename: ", filename)
        
        # local_save_path = os.path.join("output", target_character, source_motion + ".fbx")
        # os.makedirs(os.path.dirname(local_save_path), exist_ok=True)

if __name__ == "__main__":
    api = Mingle_API()

    if len(sys.argv) != 4:
        print("Usage: python script.py <target_character> <source_character> <source_motion>")
        sys.exit(1)

    argv = sys.argv
    target_character = argv[1]
    source_character = argv[2]
    source_motion = argv[3]

    api.call_retargeting_api(target_character, source_character, source_motion)
