# audiorecorder 패키지 추가 :  Streamlit 애플리케이션에서 오디오를 녹음할 수 있는 컴포넌트를 제공
# pip install streamlit-audiorecorder
from audiorecorder import audiorecorder

# streamlit: 웹 애플리케이션을 쉽게 만들 수 있는 라이브러리.
import streamlit as st

# OpenAI 패키지 추가
import openai

# os: 운영 체제와 상호 작용하기 위한 모듈.
import os
# dotenv: .env 파일에서 환경 변수를 로드하기 위한 모듈.
from dotenv import load_dotenv

# datetime: 날짜와 시간 정보를 다루기 위한 모듈.
from datetime import datetime

# 음원 파일 재생을 위한 패키지 (base64: 바이너리 데이터를 Base64 인코딩 및 디코딩하기 위한 모듈.)
import base64

from PIL import Image

# .env 파일 경로 지정 
load_dotenv()

# Open AI API 키 설정하기
api_key = os.environ.get('OPEN_API_KEY')

# OpenAi 객체생성
client = openai.OpenAI(api_key=api_key)

##### 기능 구현 함수 #####
def STT(speech):
    # 파일 저장
    filename='input.mp3'
    speech.export(filename, format="mp3")

    # 음원 파일 열기
    with open(filename, "rb") as audio_file:
        # Whisper 모델을 활용해 텍스트 얻기
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )

    # 파일 삭제
    os.remove(filename)

    return transcription.text

def ask_gpt(prompt, model):
    response = client.chat.completions.create(
        model=model, 
        messages=prompt
    )
    return response.choices[0].message.content

def TTS(text):
    filename = "output.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )

    # 음원 파일 저장
    with open(filename, "wb") as f:
        f.write(response.content)

    # 음원 파일 자동 재생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)

    # 파일 삭제
    os.remove(filename)

##### 메인 함수 #####
def main():
    # 웹페이지 상단의 탭 제목
    st.set_page_config(page_title="음성 챗봇", layout="wide",page_icon='🧛‍♀️')

    image = Image.open('image_2.png')
    st.image(image, caption='예시 이미지', use_column_width=True)   
    
    # 페이지 내부 상단의 제목
    st.header("_VOICE_  CHATBOT :blue[PROGRAM] 🎙")

    # 구분선
    st.markdown("---")


    # 기본설명
    with st.expander("음성 챗봇 프로그램에 관하여", expanded=True): # expanded는 expader의 열림(true), 닫힘(false)
        st.write(
            """
            - 음성 번역 챗봇 프로그램의 UI는 STREAMLIT을 활용합니다. 
            - STT(Speech To Text)는 Open AI의 WHISPER를 활용합니다. 
            - 답변은 Open AI의 GPT모델을 활용합니다. 
            - TTS(Text To Speech)는 Open AI의 TTS를 활용합니다. 
            """
        )
        st.markdown("")
    
        system_content = "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"

    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": system_content}]

    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    # 사이드바 생성
    with st.sidebar:
        # GPT 모델을 선택하기 위한 라디오 버튼 : 옵션 1개만 선택 
        model = st.radio(label="GPT 모델", options=["gpt-3.5-turbo","gpt-4o","gpt-4-turbo"])
        
        st.markdown("---")

        # reset 버튼 생성
        if st.button(label="초기화") :
                
                # 리셋 코드 
                st.session_state["chat"] = []
                st.session_state["messages"] = [{"role": "system", "content": system_content}]
                st.session_state["check_reset"] = True

    # 기능 구현 공간
    col1, col2 = st.columns(2)
    with col1:
        
        # 왼쪽 영역 작성
        st.subheader("질문하기")

        # 음성 녹음 아이콘 추가
        audio = audiorecorder()
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"]==False):

            # 음성 재생 
            st.audio(audio.export().read())

            # 음원 파일에서 텍스트 추출
            question = STT(audio)

            # 채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("user", now, question)]

            # GPT 모델에 넣을 프롬프트를 위해 질문 내용 저장
            st.session_state["messages"] = st.session_state["messages"] + [{"role": "user", "content": question}]

        # 텍스트 입력 추가
        text_input = st.text_input("텍스트로 질문하기")
        if text_input:
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("user", now, text_input)]
            st.session_state["messages"] = st.session_state["messages"] + [{"role": "user", "content": text_input}]

    with col2:
        # 오른쪽 영역 작성
        st.subheader("질문/답변")

        if  (audio.duration_seconds > 0 or text_input) and (st.session_state["check_reset"]==False):
            # ChatGPT에게 답변 얻기
            response = ask_gpt(st.session_state["messages"], model)

            # GPT 모델에 넣을 프롬프트를 위해 답변 내용 저장
            st.session_state["messages"] = st.session_state["messages"] + [{"role": "system", "content": response}]

            # 채팅 시각화를 위한 답변 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("bot", now, response)]

            # 채팅 형식으로 시각화 하기
            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', 
                             unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:pink;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', 
                             unsafe_allow_html=True)
                    st.write("")
                    
            # TTS 를 활용하여 음성 파일 생성 및 재생
            TTS(response)
                    
        else:
            st.session_state["check_reset"] = False

    

# 실행함수
if __name__ == "__main__" : 
    main()
