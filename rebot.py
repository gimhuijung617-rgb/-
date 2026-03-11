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

# --- 1. 설정 (토큰과 키를 입력하세요) ---
DISCORD_TOKEN = ''
GEMINI_API_KEY = ''

# Gemini 초기화 (최신 안정화 모델 사용)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') # 혹은 'gemini-1.5-pro'

# 재판 기록 저장 파일
HISTORY_FILE = "judge_history.json"

# --- 기록 로드/저장 함수 ---
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

# --- 2. 서버 헌법 데이터 ---
CONSTITUTION = """
제1조 (서버의 성격)
① 본 서버는 구성원들의 자유로운 대화와 친목을 위한 공간이다.
② 본 서버는 민주적인 운영을 원칙으로 한다.

제2조 (구성원의 권리)
① 모든 구성원은 자유롭게 대화할 권리를 가진다.
② 모든 구성원은 부당한 공격으로부터 보호받을 권리를 가진다.

제3조 (표현의 자유)
① 서버 내에서 장난, 디스, 욕설은 어느 정도 허용된다.
② 다만 다음 행위는 금지된다.

가족을 대상으로 한 모욕

지속적인 괴롭힘

제4조 (기본 질서)
① 과도한 도배는 금지한다.
② 악성 링크나 위험한 파일 공유는 금지한다.

제5조 (채널 사용 규칙)
① 각 채널은 정해진 목적에 맞게 사용한다.
② 채널 주제와 맞지 않는 대화는 자제해야 한다.

제6조 (채널 질서 유지)
① 반복적으로 채널 목적을 무시할 경우 경고를 받을 수 있다.
② 심한 경우 관리자에 의해 조치될 수 있다.

제7조 (선거)
① 서버장은 구성원의 투표로 선출한다.
② 서버장의 임기는 3개월으로 한다.

제8조 (출마 자격)
① 서버 구성원이라면 누구나 서버장 선거에 출마할 수 있다.

제9조 (투표 방식)
① 서버장은 구성원의 다수결 투표로 선출된다.

제10조 (서버장의 책임)
① 서버장은 서버 질서를 유지할 책임을 가진다.

제11조 (서버장의 권한)
① 서버장은 경고, 뮤트, 추방 등의 조치를 할 수 있다.

제12조 (권한 남용 금지)
① 서버장은 개인 감정으로 권한을 남용해서는 안 된다.

제13조 (탄핵 발의)
① 구성원 3명 이상이 동의할 경우 서버장 탄핵을 발의할 수 있다.

제14조 (탄핵 절차)
① 탄핵 발의 후 구성원의 투표를 진행한다.
② 다수의 동의를 받을 경우 서버장은 해임된다.

제15조 (임시 권한)
① 서버장이 탄핵되거나 공석일 경우 임시 관리자가 서버를 운영한다.

제16조 (처벌 단계)
① 규칙 위반 시 다음과 같은 처벌을 할 수 있다.

경고

뮤트

서버 추방

제17조 (중대한 위반)
① 패드립이나 심각한 괴롭힘은 즉시 강한 처벌을 받을 수 있다.

제18조 (분쟁 해결)
① 구성원 간 분쟁은 가능하면 개인 메시지로 해결한다.
② 필요 시 서버장이 중재할 수 있다.

제19조 (헌법 개정)
① 서버 규칙은 구성원의 의견에 따라 수정될 수 있다.

제20조 (최종 조항)
① 본 헌법은 서버 질서와 재미있는 커뮤니티 문화를 유지하기 위해 존재한다. 
"""

# --- 3. 봇 기본 설정 ---
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True # 유저 정보 파악을 위해 필요
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'⚖️ 저지맨(Gemini)이 과거의 죄업을 짊어지고 소환되었습니다!')

# --- 4. 재판 명령어 ---
@bot.command(name="재판")
async def judge(ctx, member: discord.Member, *, content: str):
    """사용법: !재판 @유저명 사건내용"""
    async with ctx.typing():
        try:
            # 1. 피고인의 전과 기록 로드
            history = load_history()
            target_id = str(member.id)
            past_judgments = history.get(target_id, [])[-3:] # 최근 3개의 판결만 참고
            past_context = "\n".join(past_judgments) if past_judgments else "전과 없음"

            # 2. 저지맨 페르소나 및 데이터 주입
            prompt = f"""
            너는 주술회전의 히구루마 히로미의 식신 '저지맨'이다. 
            아래 [서버 헌법]과 [피고인의 전과]를 근거로 현재 사건을 엄중히 심판하라.

            [피고인] {member.display_name}
            [피고인의 전과 기록]
            {past_context}

            [서버 헌법]
            {CONSTITUTION}

            [현재 사건 내용]
            {content}

            [작성 규칙]
            1. 말투는 감정이 배제된 기계적이고 차가운 문어체를 사용하라.
            2. 피고인의 전과가 있다면 "상습범"으로 간주하여 더 엄중한 처벌을 내려라.
            3. 유죄라면 반드시 '유죄(GUILTY)'라고 선언하고 위반 조항을 명시하라.
            4. 선고: [경고 / 타임아웃(1분, 5분, 10분, 1시간, 1일, 1주) / 추방] 중 택 1.
            5. 판결문 마지막은 "이상."으로 끝맺음하라.
            6. 상황이 너무 무거우면 아주 짧고 서늘한 블랙 코미디를 한 줄 섞어라.
            """

            # 3. Gemini 판결 요청
            response = model.generate_content(prompt)
            judgment_text = response.text

            # 4. 판결 결과 기록 저장 (기억 기능)
            if target_id not in history:
                history[target_id] = []
            history[target_id].append(f"사건: {content[:20]}... -> 결과: {judgment_text[:50]}...")
            save_history(history)

            # 5. 디스코드 출력
            embed = discord.Embed(
                title="⚖️ 영역 전개: 복찰자복 (伏殺者伏)", 
                description=judgment_text, 
                color=0x000000 
            )
            embed.set_footer(text=f"피고인 {member.display_name}에 대한 판결 완료")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"⚠️ 영역 전개 실패: {e}")

@bot.command(name="이의제기")
async def appeal(ctx, *, reason: str):
    """사용법: !이의제기 [이유] (방금 내린 판결에 대해 항소)"""
    async with ctx.typing():
        try:
            # 1. 기록 불러오기 (해당 유저의 마지막 판결 확인)
            history = load_history()
            user_id = str(ctx.author.id)
            
            if user_id not in history or not history[user_id]:
                await ctx.send("⚖️ 너는 아직 판결을 받은 기록이 없다. 죄부터 짓고 와라.")
                return

            last_judgment = history[user_id][-1] # 가장 최근 판결 기록

            # 2. 제미나이에게 항소심 요청
            appeal_prompt = f"""
            너는 주술회전의 저지맨이다. 피고인이 방금 내린 판결에 대해 이의를 제기했다.
            
            [원래 판결 내용]
            {last_judgment}
            
            [피고인의 이의 제기 사유]
            {reason}
            
            [지시사항]
            1. 피고인의 이유가 논리적이라면 형량을 감경해주거나 무죄로 번복하라.
            2. 만약 이유가 헛소리거나 변명에 불과하다면 '기각(REJECTED)'을 선언하고 가중 처벌을 내려라 하지만 이의제기가 충분히 부당하고 논리적이며 객관적사실을 따른다면 인정해라.
            3. 말투는 여전히 차갑고 엄격해야 한다.
            4. 마지막엔 "판결 확정."으로 끝내라.
            """

            response = model.generate_content(appeal_prompt)
            result = response.text

            # 3. 결과 출력
            embed = discord.Embed(
                title="⚖️ 이의 제기 결과 (재심)", 
                description=result, 
                color=0xff0000 if "기각" in result else 0x00ff00
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"⚠️ 이의 제기 처리 중 오류: {e}")


bot.run(DISCORD_TOKEN)


