import requests
import feedparser
from datetime import datetime
import os

# ---------- 配置区域 ----------
# 飞书 Webhook 地址（从环境变量获取）
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")

# RSS 源列表（您以后可以自己增删）
RSS_SOURCES = [
    "https://www.36kr.com/feed",           # 36氪
    "https://www.jiqizhixin.com/rss",      # 机器之心
    "https://www.infoq.cn/feed",           # InfoQ
    "https://arxiv.org/rss/cs.AI",         # arXiv AI 方向
]

# 关键词过滤（只推送包含这些词的新闻）
KEYWORDS = ["AI", "人工智能", "大模型", "数据治理", "数据资产", "埋点", "飞书", "多维表格"]
# ---------- 配置结束 ----------

def fetch_news(source_url, limit=3):
    """从单个 RSS 源获取最新新闻"""
    feed = feedparser.parse(source_url)
    entries = []
    for entry in feed.entries[:limit]:
        published = entry.get("published", datetime.now().strftime("%Y-%m-%d"))
        if len(published) > 10:
            published = published[:10]
        entries.append({
            "title": entry.title,
            "link": entry.link,
            "published": published
        })
    return entries

def filter_news(news_list):
    """根据关键词过滤新闻"""
    if not KEYWORDS:
        return news_list
    filtered = []
    for news in news_list:
        title = news["title"].lower()
        if any(keyword.lower() in title for keyword in KEYWORDS):
            filtered.append(news)
    return filtered

def build_message(news_list):
    """组装成飞书消息"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# 📰 每日行业早报 ({today})", ""]
    if not news_list:
        lines.append("今天没有匹配到相关新闻。")
    else:
        for news in news_list:
            lines.append(f"## {news['title']}")
            lines.append(f"📅 {news['published']}")
            lines.append(f"🔗 {news['link']}")
            lines.append("")
    return "\n".join(lines)

def send_to_feishu(content):
    """通过飞书机器人发送消息"""
    if not FEISHU_WEBHOOK:
        print("错误：未设置飞书 Webhook")
        return
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "每日行业早报",
                    "content": [
                        [{"tag": "text", "text": content}]
                    ]
                }
            }
        }
    }
    resp = requests.post(FEISHU_WEBHOOK, json=payload)
    if resp.status_code == 200:
        print("推送成功")
    else:
        print(f"推送失败：{resp.text}")

def main():
    all_news = []
    for url in RSS_SOURCES:
        try:
            news = fetch_news(url, limit=3)
            all_news.extend(news)
        except Exception as e:
            print(f"抓取 {url} 失败：{e}")
    
    # 去重
    seen = set()
    unique_news = []
    for news in all_news:
        if news["link"] not in seen:
            seen.add(news["link"])
            unique_news.append(news)
    
    # 关键词过滤
    filtered_news = filter_news(unique_news)
    
    # 按时间排序
    filtered_news.sort(key=lambda x: x["published"], reverse=True)
    
    # 发送
    message = build_message(filtered_news)
    send_to_feishu(message)

if __name__ == "__main__":
    main()
