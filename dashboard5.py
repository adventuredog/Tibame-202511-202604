import streamlit as st
from sqlalchemy import create_engine, Column, Integer, Float, String, Date, DateTime, Text, desc
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

# --- 1. 資料庫連線設定 (原本在 FastAPI 的部分) ---
DATABASE_URL = f"mysql+pymysql://root:{DB_PASSWORD}@localhost/macro_monitor"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. 定義 Model (與爬蟲、FastAPI 保持一致) ---
class EconomicScore(Base):
    __tablename__ = "economic_score"
    id = Column(Integer, primary_key=True)
    score_date = Column(Date)
    total_score = Column(Float)
    signal_light = Column(String(10))
    # ... 其他欄位 cpi_score, ppi_score 等依此類推

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

# --- 3. 頁面功能實作 ---

def show_economic_dashboard():
    st.title("📊 經濟健康度 (直連 MySQL 版)")
    
    db = SessionLocal()
    try:
        # 取出所有日期供下拉選單使用
        dates = db.query(EconomicScore.score_date).distinct().order_by(EconomicScore.score_date.desc()).all()
        available_dates = [str(d.score_date) for d in dates]
        
        selected_date = st.sidebar.selectbox("請選擇查詢月份", options=available_dates)
        
        if selected_date:
            data = db.query(EconomicScore).filter(EconomicScore.score_date == selected_date).first()
            
            col1, col2 = st.columns(2)
            col1.metric("綜合評分", f"{data.total_score:.1f}")
            with col2:
                sig = data.signal_light.upper()
                if sig == "RED": st.error("🔴 高風險紅燈")
                elif sig == "YELLOW": st.warning("🟡 警示黃燈")
                else: st.success("🟢 穩健綠燈")
    finally:
        db.close()

def show_news_dashboard():
    st.title("📰 美股精選新聞 (直連 MySQL 版)")
    
    days = st.sidebar.slider("幾天內新聞？", 1, 7, 3)
    limit = st.sidebar.number_input("顯示數量", 5, 50, 10)
    
    db = SessionLocal()
    try:
        time_threshold = datetime.now() - timedelta(days=days)
        top_news = db.query(NewsArticle)\
                     .filter(NewsArticle.created_at >= time_threshold)\
                     .order_by(desc(NewsArticle.importance_score))\
                     .limit(limit).all()
        
        if not top_news:
            st.warning("資料庫中尚無資料，請先執行爬蟲。")
        else:
            for news in top_news:
                with st.container():
                    col_s, col_c = st.columns([1, 6])
                    col_s.metric("重要性", f"{news.importance_score:.2f}")
                    with col_c:
                        st.subheader(f"[{news.title}]({news.link})")
                        st.caption(f"來源: {news.source} | 情緒: {news.sentiment_score:.2f}")
                        with st.expander("內容摘要"):
                            st.write(news.content)
                st.divider()
    finally:
        db.close()

# --- 4. 導航設定 ---
st.set_page_config(page_title="金融監控中心", layout="wide")

pg = st.navigation([
    st.Page(show_economic_dashboard, title="經濟指標", icon="📈"),
    st.Page(show_news_dashboard, title="美股新聞", icon="📰"),
])
pg.run()