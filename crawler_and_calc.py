import os
import sys
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# --- 配置區 ---
def send_email(subject, content):
    """使用 smtplib 寄送測試信"""
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    receiver = os.getenv("RECEIVER_EMAIL")

    if not all([sender, password, receiver]):
        print("郵件環境變數未設定，跳過寄信。")
        return

    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print("✅ 測試郵件已寄出")
    except Exception as e:
        print(f"❌ 郵件寄送失敗: {e}")

def get_fx_rate():
    """抓取最新美元對台幣匯率"""
    try:
        data = yf.download("TWD=X", period="1d", progress=False)
        return float(data['Close'].iloc[-1])
    except:
        return 31.5 # 備援值

if __name__ == "__main__":
    # 接收參數 (台灣CPI, 美國CPI)
    tw_cpi = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    us_cpi = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    
    # 自動抓取匯率
    current_fx = get_fx_rate()
    
    # 簡單加權計算 (範例)
    score = 100 - (tw_cpi * 20) - (us_cpi * 20) + (current_fx / 35 * 10)
    score = round(min(100, max(0, score)), 2)

    # 準備信件內容
    report = f"""
    【經濟監測自動化報告】
    執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}
    ---------------------------------
    手動輸入 - 台灣 CPI 月增率: {tw_cpi}%
    手動輸入 - 美國 CPI 月增率: {us_cpi}%
    自動抓取 - USD/TWD 匯率: {current_fx}
    ---------------------------------
    加權計算總分：{score}
    報告完畢。
    """
    
    print(report)
    send_email(f"經濟監測測試報告 - 分數: {score}", report)