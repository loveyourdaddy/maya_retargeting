import requests
import subprocess
import os
from functions.parser import *
    

class Mingle_API():
    def __init__(self, url='http://127.0.0.1:1236/api/'):
        self.base_url = url

    # api_endpoint ?
    def call_api(self, ):
        return requests.post(self.base_url, ) # files=files
     # files # api_endpoint, 
        # url = os.path.join(self.base_url, api_endpoint)
        # requests.post(url, json=files)

    def call_retargeting_api(self, ): # source_motion, target_character
        response = self.call_api() # 'api'
        uid = response.json()["uid"]
        result_url = os.path.join(self.base_url, uid) # api_endpoint, 
        save_path = os.path.join("output", "result.fbx")
        print("uid: ", uid)
        print("save_path:", save_path)
        print("result_url:", result_url)
        
        subprocess.run(f"curl -o {save_path} {result_url}".split(" ")) 

        # api_endpoint ?
        # files = {"dasource_motionta" : source_motion,
        #          "target_character" : target_character}

if __name__ == "__main__":
    
    api = Mingle_API()

    # import sys
    # argv = sys.argv
    # source_motion = argv[1]
    # target_character = argv[2]

    api.call_retargeting_api() # source_motion, target_character TODO: args 잘들어가는지 확인.
