import os
import sys
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def send_email(subject, content):
    # 直接從環境變數讀取
    sender = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    receiver = os.environ.get("RECEIVER_EMAIL")
    len(os.getenv("TEST_DATA"))

    # 極簡除錯判斷
    if not sender or not password or not receiver:
        print("⚠️ 錯誤：郵件環境變數缺失")
        print(f"DEBUG -> USER 長度: {len(sender) if sender else 0}")
        print(f"DEBUG -> PASS 長度: {len(password) if password else 0}")
        print(f"DEBUG -> RECV 長度: {len(receiver) if receiver else 0}")
        return

    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        # 使用 SSL 連線 Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print("✅ 郵件寄送成功！")
    except Exception as e:
        print(f"❌ 郵件寄送失敗，錯誤原因: {e}")

def get_fx_rate():
    try:
        data = yf.download("TWD=X", period="1d", progress=False)
        return float(data['Close'].iloc[-1])
    except:
        return 32.0  # 稍微調高備援值符合現況

if __name__ == "__main__":
    # 解析參數：如果沒傳參數就給 0.0
    tw_cpi = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    us_cpi = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    
    current_fx = get_fx_rate()
    
    # 簡單權重試算
    score = 100 - (tw_cpi * 20) - (us_cpi * 20) + (current_fx / 35 * 10)
    score = round(min(100, max(0, score)), 2)

    report = f"""
【經濟監測報告 - 測試版】
執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}
---------------------------------
台灣 CPI: {tw_cpi}%
美國 CPI: {us_cpi}%
美元匯率: {current_fx}
---------------------------------
加權總分：{score}
    """
    
    print(report)
    send_email(f"經濟監測報告 ({score})", report)
