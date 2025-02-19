""" 
Usage 
source char, source motion, target char, 
python retargeting_request.py ./models/Asooni/Asooni.fbx "./motions/Asooni/0048_Basic Roll_01_RT0104.fbx" ./models/Adori/Adori.fbx 
"""

import requests
import os
# from functions.parser import *
import sys

ㅠㅣㅕclass Mingle_API(): 
    # def __init__(self, url='http://127.0.0.1:5000/'): # local
    def __init__(self, url='http://183.107.15.4:5000/'): # window server 
        self.base_url = url

    def call_retargeting_api(self, target_character, source_character, source_motion): 
        # retarget api 
        upload_url = os.path.join(self.base_url, "upload_api")
        files = {
            'target_character': open(target_character, 'rb'),
            'source_character': open(source_character, 'rb'),
            'source_motion': open(source_motion, 'rb')
        }
        response = requests.post(upload_url, files=files)
        transaction_id = response.json().get('transaction_id')

        # download retargeted fbx
        download_url = os.path.join(self.base_url, 'download_api')
        headers = {'Content-Type': 'application/json'}
        download_data = {'transaction_id': transaction_id}
        download_response = requests.post(download_url, json=download_data, headers=headers)
        print(f"Download response: {download_response} transaction id {transaction_id}")

        if download_response.status_code == 200:
            # 파일 저장
            filename = download_response.headers.get('X-Filename')
            if filename:
                with open(filename, 'wb') as f:
                    f.write(download_response.content)
                print(f"File downloaded and saved as {filename}")
            else:
                print("Filename not provided in response headers")
        else:
            print("Download failed:", download_response.json())

if __name__ == "__main__":
    api = Mingle_API()

    if len(sys.argv) != 4:
        print("Usage: python script.py <source_character> <source_motion> <target_character>")
        sys.exit(1)

    argv = sys.argv
    source_character = argv[1]
    source_motion = argv[2]
    target_character = argv[3]

    api.call_retargeting_api(target_character, source_character, source_motion)
