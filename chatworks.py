#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
chatworks.py - 改善版

毎朝9時に日本語の"AI"関連記事タイトル＋リンクを取得し、
指定のChatWorkルームへ投稿するスクリプト。

改善点:
- ニュース配信数を5件に最適化
- AIキーワードを最新トレンドに特化
- RSSフィードを高品質ソースに厳選
- スコアリング機能を強化

事前準備:
    pip install requests beautifulsoup4[lxml]
"""

import sys
import logging
import requests
import os
from datetime import datetime
from bs4 import BeautifulSoup

# ——— 環境変数から設定を取得 ———
CHATWORK_TOKEN   = os.environ.get("CHATWORK_TOKEN")
CHATWORK_ROOM_ID = os.environ.get("CHATWORK_ROOM_ID")
NEWS_LIMIT       = 5  # 🔥 改善: 8件から5件に変更

# 設定チェック
if not CHATWORK_TOKEN or not CHATWORK_ROOM_ID:
    logging.error("環境変数 CHATWORK_TOKEN と CHATWORK_ROOM_ID を設定してください")
    sys.exit(1)

# 🔥 改善: 厳選された高品質RSSフィード
FEED_URLS = [
    # トップニュースサイト
    "https://news.google.com/rss/search?q=AI&hl=ja&gl=JP&ceid=JP:ja",
    "https://news.yahoo.co.jp/rss/topics/it.xml",
    
    # 主要IT専門メディア
    "https://rss.itmedia.co.jp/rss/2.0/itmedia_aiplus.xml",
    "https://rss.itmedia.co.jp/rss/2.0/itmedia_news.xml",
    "https://gigazine.net/news/rss_2.0/",
    "https://ascii.jp/rss.xml",
    
    # 技術系トップメディア
    "https://www.publickey1.jp/atom.xml",
    "https://xtech.nikkei.com/rss/index.rdf",
    "https://gihyo.jp/feed/rss2",
    
    # ビジネス・経済系
    "https://toyokeizai.net/list/feed/rss",
    "https://diamond.jp/list/feed/rss",
    
    # AI特化・開発者向け
    "https://ainow.ai/feed/",
    "https://qiita.com/popular-items/feed",
    "https://zenn.dev/feed",
    
    # 企業テックブログ（選抜）
    "https://developers.cyberagent.co.jp/blog/feed/",
]

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def get_source_name(url: str) -> str:
    """URLから情報源の名前を取得（簡略化）"""
    source_mapping = {
        "news.google.com": "Google ニュース",
        "news.yahoo.co.jp": "Yahoo! ニュース",
        "itmedia.co.jp": "ITmedia",
        "gigazine.net": "GIGAZINE",
        "ascii.jp": "ASCII.jp",
        "publickey1.jp": "Publickey",
        "xtech.nikkei.com": "日経クロステック",
        "gihyo.jp": "技術評論社",
        "toyokeizai.net": "東洋経済",
        "diamond.jp": "ダイヤモンド",
        "ainow.ai": "AINOW",
        "qiita.com": "Qiita",
        "zenn.dev": "Zenn",
        "developers.cyberagent.co.jp": "CyberAgent",
    }
    
    for domain, name in source_mapping.items():
        if domain in url:
            return name
    return "その他"

def fetch_ai_news(limit: int = NEWS_LIMIT) -> list[dict]:
    """AI関連記事を取得"""
    articles = []
    successful_feeds = 0
    failed_feeds = 0
    
    for url in FEED_URLS:
        try:
            logging.info(f"Fetching feed: {url}")
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=15, verify=True)
            resp.raise_for_status()
            successful_feeds += 1
        except Exception as e:
            logging.warning(f"フィード取得失敗 ({get_source_name(url)}): {e}")
            failed_feeds += 1
            continue

        try:
            soup = BeautifulSoup(resp.content, "xml")
            source_name = get_source_name(url)
            
            # RSS の item
            for item in soup.find_all("item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get_text(strip=True)
                    
                    if title and link:
                        articles.append({
                            "title": title,
                            "link": link,
                            "source": source_name
                        })
            
            # Atom の entry
            for entry in soup.find_all("entry"):
                title_elem = entry.find("title")
                link_elem = entry.find("link", rel="alternate") or entry.find("link")
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = ""
                    
                    if link_elem:
                        if link_elem.has_attr("href"):
                            link = link_elem["href"].strip()
                        else:
                            link = link_elem.get_text(strip=True)
                    
                    if title and link:
                        articles.append({
                            "title": title,
                            "link": link,
                            "source": source_name
                        })
                        
        except Exception as e:
            logging.warning(f"フィード解析失敗 ({get_source_name(url)}): {e}")

    logging.info(f"フィード取得結果: 成功 {successful_feeds}件, 失敗 {failed_feeds}件")

    # 🔥 改善: シンプルで効果的なAIキーワード（最新トレンド）
    ai_keywords = [
        # 基本キーワード
        "ai", "ＡＩ", "人工知能", "機械学習", "深層学習",
        
        # 生成AI・LLMトレンド
        "生成ai", "生成ＡＩ", "大規模言語モデル", "llm",
        
        # 主要AIサービス
        "chatgpt", "チャットgpt", "gpt", "claude", "gemini",
        
        # 企業・技術
        "openai", "anthropic", "google ai", "transformer",
        
        # 応用分野
        "画像生成", "aiライティング", "自動化", "チャットボット"
    ]
    
    filtered = []
    for article in articles:
        title_lower = article["title"].lower()
        if any(keyword in title_lower for keyword in ai_keywords):
            filtered.append(article)

    # 🔥 改善: より精密なスコアリング機能
    def calculate_ai_score(title):
        title_lower = title.lower()
        score = 0
        
        # 最高優先度キーワード
        ultra_priority = ["chatgpt", "gpt-4", "claude", "gemini", "生成ai"]
        high_priority = ["openai", "anthropic", "大規模言語モデル", "llm"]
        medium_priority = ["ai", "ＡＩ", "人工知能", "機械学習"]
        
        for keyword in ultra_priority:
            if keyword in title_lower:
                score += 5
        for keyword in high_priority:
            if keyword in title_lower:
                score += 3
        for keyword in medium_priority:
            if keyword in title_lower:
                score += 1
        
        return score
    
    # 重複排除とスコア順ソート
    seen_urls = set()
    seen_titles = set()
    unique = []
    
    filtered.sort(key=lambda x: calculate_ai_score(x["title"]), reverse=True)
    
    for article in filtered:
        if article["link"] in seen_urls:
            continue
        
        title_key = article["title"][:30].strip()
        if title_key in seen_titles:
            continue
        
        seen_urls.add(article["link"])
        seen_titles.add(title_key)
        unique.append(article)
        
        if len(unique) >= limit:
            break

    logging.info(f"Selected {len(unique)} AI articles from {len(filtered)} filtered articles")
    return unique

def post_to_chatwork(message: str) -> None:
    """ChatWorkへメッセージ投稿"""
    url = f"https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/messages"
    headers = {
        "X-ChatWorkToken": CHATWORK_TOKEN,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {"body": "[toall]\n" + message}
    resp = requests.post(url, headers=headers, data=data)
    resp.raise_for_status()

def build_news_message(articles: list[dict]) -> str:
    """AIニュース一覧メッセージを作成"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M")
    
    sources = {}
    for article in articles:
        source = article.get("source", "不明")
        sources[source] = sources.get(source, 0) + 1
    
    message_parts = [
        f"[info][title]🤖 本日のAIニュース - {current_date}[/title]",
        f"📅 配信時刻: {current_time}",
        f"📊 記事数: {len(articles)}件（厳選版）",
        f"📡 情報源: {len(sources)}サイト",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ""
    ]
    
    for i, article in enumerate(articles, 1):
        title = article['title']
        if len(title) > 75:
            title = title[:72] + "..."
        
        source = article.get('source', '不明')
        
        message_parts.extend([
            f"📰 【記事 {i}】({source})",
            f"💡 {title}",
            f"🔗 {article['link']}",
            ""
        ])
    
    if len(sources) > 1:
        message_parts.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📈 主要情報源:",
            ""
        ])
        
        sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]
        for source, count in sorted_sources:
            message_parts.append(f"　• {source}: {count}件")
        
        message_parts.append("")
    
    message_parts.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "✨ 厳選された最新AI情報をお届けしました！",
        "📱 気になる記事があればリンクをクリックしてご覧ください。",
        "[/info]"
    ])
    
    return "\n".join(message_parts)

def build_no_news_message() -> str:
    """記事が見つからない場合のメッセージ"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M")
    
    return (
        f"[info][title]🤖 本日のAIニュース - {current_date}[/title]\n"
        f"📅 配信時刻: {current_time}\n"
        f"📊 記事数: 0件\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 申し訳ございません。本日は新しいAI関連記事が見つかりませんでした。\n"
        f"📰 明日また最新情報をお届けいたします！\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"[/info]"
    )

def build_error_message() -> str:
    """エラー発生時のメッセージ"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M")
    
    return (
        f"[info][title]⚠️ システム通知 - {current_date}[/title]\n"
        f"📅 通知時刻: {current_time}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🚨 AIニュース配信でエラーが発生しました。\n"
        f"🔧 システム管理者にご確認ください。\n"
        f"🕐 次回の配信をお待ちください。\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"[/info]"
    )

def main():
    try:
        news_list = fetch_ai_news()
        
        if not news_list:
            logging.warning("取得できたAI記事がありませんでした。")
            no_news_msg = build_no_news_message()
            post_to_chatwork(no_news_msg)
            return

        unified_msg = build_news_message(news_list)
        post_to_chatwork(unified_msg)
        
        logging.info(f"AIニュース {len(news_list)}件を一括投稿しました。")
        
    except Exception as e:
        logging.exception("スクリプト実行中にエラーが発生しました。")
        error_msg = build_error_message()
        try:
            post_to_chatwork(error_msg)
        except:
            logging.error("エラー通知の投稿にも失敗しました。")

if __name__ == "__main__":
    main()
