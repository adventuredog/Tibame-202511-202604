import feedparser
from newspaper import Article
from textblob import TextBlob
from datetime import datetime
import time
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# --- 1. 資料庫連線設定 (與你的 FastAPI 一致) ---
DATABASE_URL = "mysql+pymysql://root:Chenszuhan120!@localhost/macro_monitor"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. 定義 Model (必須與 FastAPI 那邊定義的一模一樣) ---
class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    link = Column(String(500), unique=True)
    source = Column(String(50))
    content = Column(Text)
    sentiment_score = Column(Float)
    importance_score = Column(Float)
    published = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)

RSS_FEEDS = {
    'CNN Business': 'http://rss.cnn.com/rss/money_latest.rss',
    'BBC Business': 'http://feeds.bbci.co.uk/news/business/rss.xml',
    'Yahoo Finance': 'https://finance.yahoo.com/news/rssindex'
}

def get_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    return (polarity + 1) / 2  # 轉為 0~1 分數

def calculate_importance(content, sentiment_score):
    keywords = ['fed','inflation','nvidia','apple','rate cut','earnings','fomc']
    hit_count = sum(1 for word in keywords if word in content.lower())
    kw_score = min(hit_count / 3, 1.0)
    total_score = (0.4 * sentiment_score) + (0.4 * kw_score) + (0.2 * min(len(content)/800, 1.0))
    return round(total_score, 3)

def main():
    db = SessionLocal()
    print("--- 開始抓取新聞 ---")
    try:
        for name, url in RSS_FEEDS.items():
            print(f"正在掃描 {name}...")
            feed = feedparser.parse(url)

            for entry in feed.entries[:10]:
                link = entry.link
                
                # --- 關鍵：檢查資料庫是否已有此連結 (去重) ---
                if db.query(NewsArticle).filter(NewsArticle.link == link).first():
                    continue

                try:
                    article = Article(link)
                    article.download()
                    article.parse()

                    title = entry.title
                    content = article.text
                    sent_score = get_sentiment(title)
                    imp_score = calculate_importance(content, sent_score)

                    # --- 寫入 MySQL ---
                    new_news = NewsArticle(
                        title=title[:250],
                        link=link,
                        source=name,
                        content=content[:500],
                        sentiment_score=sent_score,
                        importance_score=imp_score,
                        published=entry.get('published', ''),
                        created_at=datetime.now()
                    )
                    db.add(new_news)
                    db.commit()
                    print(f"✅ 已匯入: {title[:30]}...")
                    time.sleep(1)
                except Exception as e:
                    db.rollback()
                    print(f"❌ 解析失敗: {e}")
    finally:
        db.close()
    print("--- 任務結束 ---")

if __name__ == "__main__":
    main()