import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

# --- 엑셀을 대체하는 내장 QnA 매뉴얼 ---
QNA_DATA = {
    "배송": "안녕하세요! 평일 5시 이전 주문건은 대부분 다음날 도착합니다.",
    "취소": "취소 처리는 즉시 승인되며, 영업일 기준 1~3일 내에 환불됩니다."
}

# --- 클라우드에 숨겨둘 환경 변수(API 키) 불러오기 ---
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_SECRET = os.environ.get("NAVER_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    """텔레그램으로 핸드폰 알림을 쏘는 함수"""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def run_bot():
    """24시간 무한 반복되는 봇의 핵심 업무 로직"""
    time.sleep(5) # 서버 켜지고 잠시 대기
    send_telegram("🚀 24시간 무인 봇 서버가 클라우드에서 가동을 시작했습니다!")
    
    while True:
        try:
            # 이곳에 네이버 API 문의 조회 및 답변 로직이 자동으로 반복됩니다.
            # (기존에 작성하신 네이버/구글 API 핵심 로직 구동)
            print("네이버 스마트스토어 순찰 중...")
            
        except Exception as e:
            print(f"오류 발생: {e}")
            send_telegram(f"⚠️️ 봇 에러 발생: {e}")
        
        time.sleep(60) # 1분마다 순찰

# --- UptimeRobot이 5분마다 찔러줄 생명줄(Health Check) 주소 ---
@app.route('/health')
def health():
    return "봇이 24시간 정상적으로 깨어 있습니다!", 200

if __name__ == '__main__':
    # 봇 로직을 백그라운드 스레드로 분리하여 무한 실행
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # 렌더 클라우드용 웹 서버 가동
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)