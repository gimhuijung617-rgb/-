import discord
from discord.ext import commands
import google.generativeai as genai
import json
import os

from flask import Flask
from threading import Thread

# --- [추가 2] 가짜 웹 서버 설정 ---
app = Flask('')

@app.route('/')
def home():
    return "저지맨/머시깽이가 24시간 감시 중입니다!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 1. 설정 ---
DISCORD_TOKEN = '='
GEMINI_API_KEY = 'A'

# Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 대화 기록 저장 파일
HISTORY_FILE = "chat_history.json"

# --- 기록 로드/저장 함수 ---
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

# --- 2. 서버 헌법 ---
CONSTITUTION = "욕좀 해도 되는데 선넘지 말고 눈치좀 쳐라"

# --- 3. 봇 기본 설정 ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 머시깽이 등장')

# --- 4. 메인 명령어 ---
@bot.command(name="머시깽이")
async def judge(ctx, *, content: str):
    async with ctx.typing():
        try:
            # 과거 기록 불러오기
            history = load_history()
            user_id = str(ctx.author.id)
            
            # 이 유저의 이전 대화 가져오기 (없으면 빈 리스트)
            past_chats = history.get(user_id, [])[-5:] # 최신 5개 대화만 기억 (너무 많으면 헷갈려함)
            context_text = "\n".join(past_chats)

            # 프롬프트 구성
            prompt = f"""
            너는 무엇을 물어보든지 말해주는 똑똑한 '머시깽이'다.
            
            [이전 대화 기록]
            {context_text}

            [서버 헌법]
            {CONSTITUTION}

            [현재 질문]
            {content}

            [작성 규칙]
            1. 부랄친구같은 말투를 사용해라.
            2. 개그도 좀 쳐라.
            3. 너는 인간이다.
            4. 이전 대화 기록을 참고해서 문맥에 맞게 대답해라.
            5. 작성 규칙을 병적으로 사용하지마라 어색해 보인다.
            """

            # Gemini 호출 (Groq 방식이 아닌 Gemini 방식으로 수정)
            response = model.generate_content(prompt)
            reply = response.text

            # 대화 기록 업데이트 및 저장
            new_chat = f"질문: {content} -> 답변: {reply}"
            if user_id not in history:
                history[user_id] = []
            history[user_id].append(new_chat)
            save_history(history)

            # 출력
            embed = discord.Embed(title="음..", description=reply, color=0x2c2f33)
            embed.set_footer(text=".")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"⚠️ 야 오류났다 꺼져: {e}")


bot.run(DISCORD_TOKEN)


