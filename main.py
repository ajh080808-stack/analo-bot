import os
import time
import threading
import requests
import bcrypt
import base64
from flask import Flask

app = Flask(__name__)

QNA_DATA = {
    "무음": "안녕하세요 고객님! 무음 제품을 희망하시는 경우, 구매 전 톡톡 문의 또는 배송 메모에 '무음 제품 희망'이라고 남겨주시면 확인 후 무음 제품으로 발송해 드리겠습니다!",
    "소리": "안녕하세요 고객님! 무음 제품을 희망하시는 경우, 구매 전 톡톡 문의 또는 배송 메모에 '무음 제품 희망'이라고 남겨주시면 확인 후 무음 제품으로 발송해 드리겠습니다!",
    "유심": "안녕하세요 고객님! 쓰시던 유심이나 새로 구매하신 유심(알뜰폰 포함 3사 모두 가능)을 꽂으시면 메인폰, 세컨폰 상관없이 통화/문자 모두 즉시 정상 사용 가능한 자급제 단말기입니다!",
    "자급제": "안녕하세요 고객님! 쓰시던 유심이나 새로 구매하신 유심(알뜰폰 포함 3사 모두 가능)을 꽂으시면 메인폰, 세컨폰 상관없이 통화/문자 모두 즉시 정상 사용 가능한 자급제 단말기입니다!",
    "애플아이디": "안녕하세요 고객님! 애플 아이디 생성 및 에어드롭 등 아이폰의 모든 고유 기능은 정상적으로 100% 사용 가능합니다!",
    "에어드롭": "안녕하세요 고객님! 애플 아이디 생성 및 에어드롭 등 아이폰의 모든 고유 기능은 정상적으로 100% 사용 가능합니다!",
    "16": "안녕하세요 고객님! 전화와 문자 등 기본 용도로만 사용하신다면 16GB 모델로도 충분히 쾌적하게 사용 가능하십니다. 다만 사진을 많이 찍으신다면 32GB를 추천해 드립니다!",
    "32": "안녕하세요 고객님! 전화와 문자 등 기본 용도로만 사용하신다면 16GB 모델로도 충분히 쾌적하게 사용 가능하십니다. 다만 사진을 많이 찍으신다면 32GB를 추천해 드립니다!",
    "배송": "안녕하세요 고객님! 국내배송으로 배송기간은 평일 5시 이전 주문건은 도서산간 지역을 제외하고 대부분 다음날 받아보실 수 있습니다!",
    "도착": "안녕하세요 고객님! 국내배송으로 배송기간은 평일 5시 이전 주문건은 도서산간 지역을 제외하고 대부분 다음날 받아보실 수 있습니다!"
}

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "").strip()
NAVER_SECRET = os.environ.get("NAVER_SECRET", "").strip()
NAVER_ACCOUNT_ID = os.environ.get("NAVER_ACCOUNT_ID", "").strip()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

def send_telegram(message):
    try:
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=5)
    except Exception as e:
        print(f"텔레그램 발송 실패: {e}", flush=True)

def get_naver_token():
    timestamp = int(time.time() * 1000)
    password = NAVER_CLIENT_ID + "_" + str(timestamp)
    hashed = bcrypt.hashpw(password.encode('utf-8'), NAVER_SECRET.encode('utf-8'))
    signature = base64.b64encode(hashed).decode('utf-8')
    
    url = "https://api.commerce.naver.com/external/v1/oauth2/token"
    data = {
        "client_id": NAVER_CLIENT_ID,
        "timestamp": timestamp,
        "client_secret_sign": signature,
        "grant_type": "client_credentials",
        "type": "SELLER",
        "account_id": NAVER_ACCOUNT_ID
    }
    res = requests.post(url, data=data, timeout=10)
    
    # 💡 에러 발생 시 네이버의 진짜 거절 사유를 까만 창에 출력합니다!
    if res.status_code != 200:
        print(f"🚨 네이버 로그인 거절 상세 이유: {res.text}", flush=True)
        
    res.raise_for_status()
    return res.json().get("access_token")

def find_answer(question):
    question_no_space = question.replace(" ", "")
    for keyword, answer in QNA_DATA.items():
        if keyword in question_no_space:
            return answer
    return None

def run_bot():
    time.sleep(5)
    send_telegram("🚀 스마트스토어 24시간 CS 봇이 완전히 깨어났습니다! 밀린 문의 순찰을 시작합니다.")
    
    while True:
        try:
            print("네이버 스마트스토어 순찰 중...", flush=True)
            token = get_naver_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            url = "https://api.commerce.naver.com/external/v1/contents/qnas?page=1&size=20"
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            qnas = res.json()
            
            contents = qnas.get('content', []) if 'content' in qnas else (qnas.get('elements', []) if 'elements' in qnas else qnas)
            
            if isinstance(contents, list):
                for qna in contents:
                    is_answered = qna.get('answered', False) or qna.get('answerStatus') == 'ANSWERED'
                    if is_answered:
                        continue
                        
                    question_id = qna.get('questionId', qna.get('id'))
                    question_title = str(qna.get('subject', qna.get('title', ''))) 
                    question_body = str(qna.get('content', ''))
                    question_text = question_title + " " + question_body
                    
                    if not question_id:
                        continue
                        
                    print(f"미답변 문의 발견: {question_text}", flush=True)
                    answer = find_answer(question_text)
                    
                    if answer:
                        print(f"✅ 매뉴얼 매칭 완료! 답변 등록 시도 중...", flush=True)
                        put_url = f"https://api.commerce.naver.com/external/v1/contents/qnas/{question_id}"
                        put_data = {"answerContent": answer}
                        headers['Content-Type'] = 'application/json'
                        
                        put_res = requests.put(put_url, headers=headers, json=put_data, timeout=10)
                        
                        if put_res.status_code == 200:
                            send_telegram(f"✅ 스마트스토어 자동 답변 완료!\n\n[문의] {question_text[:20]}...\n[답변] {answer[:30]}...")
                            print(f"답변 등록 완료: {question_id}", flush=True)
                        else:
                            print(f"답변 등록 실패: {put_res.text}", flush=True)
                    else:
                        print("등록된 매뉴얼에 해당되는 키워드가 없어 대기합니다.", flush=True)
            
        except Exception as e:
            pass # 불필요한 중복 에러 로그는 가림 처리
            
        time.sleep(60)

bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

@app.route('/health')
def health():
    return "봇이 24시간 정상적으로 깨어 있습니다!", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
