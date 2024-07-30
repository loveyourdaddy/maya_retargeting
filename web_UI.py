import gradio as gr 

def user_greeting(name):
    return "안녕하세요! " + name + "님, 첫 번째 Gradio 애플리케이션에 오신 것을 환영합니다!😎"

app = gr.Interface(fn=user_greeting, inputs="text", outputs="text")
app.launch()

"""
TODO functions 
1. upload fbx 
2. run code 
3. download fbx

local host -> 외부에서 접속가능하게 하기
- External port을 열고, ip:port 형태로 외부에서 접속 확인
"""