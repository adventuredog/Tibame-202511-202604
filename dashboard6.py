# 不連接地端MySQL而是連接SQLite的版本，已經上傳到 GitHub，請參考 dashboard6.py
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, Float, String, Date, DateTime, Text, desc
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timedelta
import os

# --- 1. 資料庫連線設定 (SQLite 檔案) ---
DB_FILE = "local_data.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

# 建立引擎與 Session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. 定義資料表模型 (必須與轉換時的結構一致) ---
class EconomicScore(Base):
    __tablename__ = "economic_score"
    id = Column(Integer, primary_key=True)
    score_date = Column(Date)
    cpi_score = Column(Float)
    ppi_score = Column(Float)
    fx_score = Column(Float)
    total_score = Column(Float)
    signal_light = Column(String(10))

class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    link = Column(String(500))
    source = Column(String(50))
    content = Column(Text)
    sentiment_score = Column(Float)
    importance_score = Column(Float)
    created_at = Column(DateTime)

# --- 頁面 1: 經濟儀表板 ---
def show_economic_dashboard():
    st.title("📊 經濟健康度儀表板 (SQLite)")
    
    if not os.path.exists(DB_FILE):
        st.error(f"找不到資料庫檔案 {DB_FILE}，請確認檔案已在目錄中。")
        return

    db = SessionLocal()
    try:
        # 取出所有日期
        results = db.query(EconomicScore.score_date).distinct().order_by(EconomicScore.score_date.desc()).all()
        available_dates = [str(r.score_date) for r in results]

        st.sidebar.header("查詢條件")
        selected_date = st.sidebar.selectbox("請選擇查詢月份", options=available_dates)

        if selected_date:
            # 直接查詢資料庫
            data = db.query(EconomicScore).filter(EconomicScore.score_date == selected_date).first()
            
            if data:
                col1, col2 = st.columns(2)
                with col1: 
                    st.metric(label="綜合評分", value=f"{data.total_score:.1f}")
                with col2:
                    sig = data.signal_light.upper()
                    if sig == "RED": st.error("🔴 高風險紅燈")
                    elif sig == "YELLOW": st.warning("🟡 警示黃燈")
                    else: st.success("🟢 穩健綠燈")
                
                with st.expander("詳細數據"):
                    st.write({
                        "date": str(data.score_date),
                        "cpi": data.cpi_score,
                        "ppi": data.ppi_score,
                        "fx": data.fx_score,
                        "total": data.total_score,
                        "signal": data.signal_light
                    })
    finally:
        db.close()

# --- 頁面 2: 美股新聞 ---
def show_news_dashboard():
    st.title("📰 每日美股精選新聞 (SQLite)")
    
    with st.sidebar:
        st.title("新聞面板")
        days = st.slider("幾天內新聞？", 1, 7, 3)
        limit_count = st.number_input("顯示數量", 5, 50, 10)

    db = SessionLocal()
    try:
        time_threshold = datetime.now() - timedelta(days=days)
        # 直接從 SQLite 篩選與排序
        top_news = db.query(NewsArticle)\
                     .filter(NewsArticle.created_at >= time_threshold)\
                     .order_by(desc(NewsArticle.importance_score))\
                     .limit(limit_count).all()

        if not top_news:
            st.warning("暫無新聞資料。")
        else:
            for news in top_news:
                with st.container():
                    col_s, col_c = st.columns([1, 6])
                    col_s.metric("重要性", f"{news.importance_score:.2f}")
                    with col_c:
                        st.subheader(f"[{news.title}]({news.link})")
                        c1, c2 = st.columns(2)
                        c1.write(f"🔹 來源: {news.source}")
                        sent = news.sentiment_score
                        emoji = "正向" if sent > 0.6 else "中性" if sent > 0.4 else "負向"
                        c2.write(f"🎭 情緒: {emoji} ({sent:.2f})")
                        with st.expander("摘要"): 
                            st.write(news.content)
                st.divider()
    finally:
        db.close()

# --- 導航主邏輯 ---
st.set_page_config(page_title="金融監控系統", layout="wide")

pg = st.navigation([
    st.Page(show_economic_dashboard, title="經濟健康度", icon="📈"),
    st.Page(show_news_dashboard, title="美股精選新聞", icon="📰"),
])
pg.run()