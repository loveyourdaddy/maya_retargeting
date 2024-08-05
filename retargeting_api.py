from fastapi import FastAPI
from fastapi.responses import FileResponse # JSONResponse,
import uvicorn

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8000",
]

@app.get("/api")
async def read_root():
    return "This is root path for Mingle-AI api"

@app.post("/api/{uid}")
async def call_retargeting_func(target_character, source_motion): # uid:str
    # download retargeted fbx 
    from retargeting_different_axis import main
    # 명령어 형태로 실행 
    main(target_character, source_motion) # TODO: check argument 
    {"message": "retargeting process is done."}

    # Return as file 
    return FileResponse(path=f"output/{target_character}/{source_motion}.fbx", filename="bear.gltf", media_type="application/octet-stream")
    # filename 이 또 필요한 이유?

if __name__ == "__main__":
    # 
    uvicorn.run(app, host="0.0.0.0", port=8077) # key 확인
    # ssl_keyfile="./../../selfcert/key.pem" 
    # ssl_certfile="./../../selfcert/certificate.pem"

# uvicorn api:app --port 8080 --reload
# curl http://127.0.0.1:8080/

# Difference: 
# get: 서버에서 데이터를 가져오기 
# post: 서버에 데이터 전송하여 상태 변경 