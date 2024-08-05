from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import base64
from google_text_to_speech.google_translate_tts import split_text, generate_url
import requests
import tempfile

import subprocess
import uvicorn
import os
from io import BytesIO
from a2f_inf import load_model, audio2face
from a2f_emo import emotion_extractor

from pydantic import BaseModel
import librosa
import soundfile as sf
import noisereduce as nr

app = FastAPI()

allowed_origins = [
    "http://0.0.0.0:8073",
    "https://0.0.0.0:8073",
    "http://localhost:8073",
    "http://127.0.0.1:8073",
    "https://localhost:8073",
    "https://127.0.0.1:8073",
    "https://183.107.15.2:8073"
    "https://143.248.249.84:8073"
    "http://143.248.249.84:8073"
    # Add other origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

a2v_model = load_model('models/checkpoints/wav2lip_gan.pth',True)
v2m_model = load_model('models/checkpoints/best_epoch37_orig.pt',False)
emo_extract =  emotion_extractor()

class TextData(BaseModel):
    textData: str


async def convert_audio_to_wav(webm_data: bytes) -> BytesIO:
    # No need to encode webm_data, as it's already in bytes
    process = subprocess.run(
        ['ffmpeg', '-i', 'pipe:0', '-ar', '16000', '-ac', '1', '-f', 'wav', 'pipe:1'],
        input=webm_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if process.returncode != 0:
        # Decode stderr from bytes to string for JSON serialization
        error_message = process.stderr.decode('utf-8')
        raise Exception(f"Error in ffmpeg processing: {error_message}")

    # Directly use process.stdout, which is already a bytes object
    wav_io = BytesIO(process.stdout)
    return wav_io


@app.post("/home/kai/Documents/audio2face/")
async def upload_audio(audioFile: UploadFile = File(...)):
    global a2v_model,v2m_model

    webm_data = await audioFile.read()
    wav_io = await convert_audio_to_wav(webm_data)
    wav_io.seek(0)  # Ensure we're at the start
    data, samplerate = sf.read(wav_io)
    if samplerate != 16000:
        data = librosa.resample(data, orig_sr=samplerate, target_sr=target_sr)

    #data = librosa.core.load('SPKF001.wav', sr=16000)[0]

    int_data = (data * 32768).astype('int16')

    intwav = nr.reduce_noise(y=int_data, sr=16000)
    wav = intwav/32768.0

    #sf.write('ori2.wav', data, 16000)
    #sf.write('rm2.wav', wav, 16000)

    emotion_value= emo_extract.emo_feature(signal)
    latent=audio2face(a2v_model,v2m_model,wav=wav)
    print(f"latent shape is {latent.shape}")
    latent_list = latent.tolist()
    emothis_list = emotion_value.tolist()
    wav_io2write = BytesIO()
    sf.write(wav_io2write, intwav, 16000, format='WAV')
    wav_io2write.seek(0)
    base64_wav_data = base64.b64encode(wav_io2write.read()).decode('utf-8')

    # response
    return JSONResponse(status_code=200, content={
        "message": "File uploaded successfully",
        "filename": textData,
        "latent": latent_list,
        "emotion": emothis_list,
        "wavData": base64_wav_data
    })


if __name__ == "__main__":
     uvicorn.run(app, host="0.0.0.0", port=8077, ssl_keyfile="./../../selfcert/key.pem", ssl_certfile="./../../selfcert/certificate.pem")
     #uvicorn.run(app, host="0.0.0.0", port=8076, ssl_keyfile="/etc/letsencrypt/live/service.mingle-ai.com/privkey.pem", ssl_certfile="/etc/letsencrypt/live/service.mingle-ai.com/fullchain.pem")
     #uvicorn.run(app, host="0.0.0.0", port=8076)
