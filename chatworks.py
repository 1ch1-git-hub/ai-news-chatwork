#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
chatworks.py

毎朝9時に日本語の"AI"関連記事タイトル＋リンクを取得し、
指定のChatWorkルームへ投稿するスクリプト。

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
NEWS_LIMIT       = 8

# 設定チェック
if not CHATWORK_TOKEN or not CHATWORK_ROOM_ID:
    logging.error("環境変数 CHATWORK_TOKEN と CHATWORK_ROOM_ID を設定してください")
    sys.exit(1)

# ——————————————

# 日本語サイトのRSSフィード（動作確認済みのURLに修正）
FEED_URLS = [
    # 主要ニュースサイト
    "https://news.google.com/rss/search?q=AI&hl=ja&gl=JP&ceid=JP:ja",
    "https://news.yahoo.co.jp/rss/topics/it.xml",
    "https://feeds.reuters.com/reuters/JPtechnologyNews",
    
    # IT系専門メディア（動作確認済み）
    "https://rss.itmedia.co.jp/rss/2.0/itmedia_news.xml",
    "https://rss.itmedia.co.jp/rss/2.0/itmedia_aiplus.xml",
    "http://feed.japan.cnet.com/rss/index.rdf",
    "https://ascii.jp/rss.xml",
    "https://www.watch.impress.co.jp/data/rss/1.0/ipw/feed.rdf",
    "https://internet.watch.impress.co.jp/data/rss/1.0/iw/feed.rdf",
    "https://pc.watch.impress.co.jp/data/rss/1.0/pcw/feed.rdf",
    "https://akiba-pc.watch.impress.co.jp/data/rss/1.0/ah/feed.rdf",
    "https://forest.watch.impress.co.jp/data/rss/1.0/wf/feed.rdf",
    "https://gigazine.net/news/rss_2.0/",
    
    # 技術系メディア（動作確認済み）
    "https://www.publickey1.jp/atom.xml",
    "https://codezine.jp/rss/new/20/index.xml",
    "https://gihyo.jp/feed/rss2",
    "https://xtech.nikkei.com/rss/index.rdf",
    "https://weekly.ascii.jp/rss.xml",
    
    # ビジネス・経済系（動作確認済み）
    "https://toyokeizai.net/list/feed/rss",
    "https://diamond.jp/list/feed/rss",
    
    # スタートアップ・IT系
    "https://thebridge.jp/feed",
    "https://www.sbbit.jp/rss/HotTopics.rss",
    
    # AI特化メディア
    "https://ainow.ai/feed/",
    
    # 企業ブログ・テックブログ（動作確認済み）
    "https://developers.cyberagent.co.jp/blog/feed/",
    "https://techblog.yahoo.co.jp/atom.xml",
    "https://developer.hatenastaff.com/rss",
    "https://blog.recruit.co.jp/rtc/feed/",
    
    # 追加の技術系サイト
    "https://qiita.com/popular-items/feed",
    "https://zenn.dev/feed",
    
    # 大学・研究機関
    "https://resou.osaka-u.ac.jp/ja/rss.xml",
    
    # その他のIT系メディア
    "https://it.srad.jp/srad.rdf",
    "https://japan.zdnet.com/rss/index.rdf",
]

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/102.0.0.0 Safari/537.36"
    )
}

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)


def get_source_name(url: str) -> str:
    """
    URLから情報源の名前を取得
    """
    source_mapping = {
        "news.google.com": "Google ニュース",
        "news.yahoo.co.jp": "Yahoo! ニュース",
        "feeds.reuters.com": "Reuters Japan",
        "itmedia.co.jp": "ITmedia",
        "feed.japan.cnet.com": "CNET Japan",
        "ascii.jp": "ASCII.jp",
        "watch.impress.co.jp": "Impress Watch",
        "internet.watch.impress.co.jp": "INTERNET Watch", 
        "pc.watch.impress.co.jp": "PC Watch",
        "akiba-pc.watch.impress.co.jp": "AKIBA PC Hotline!",
        "forest.watch.impress.co.jp": "窓の杜",
        "gigazine.net": "GIGAZINE",
        "publickey1.jp": "Publickey",
        "codezine.jp": "CodeZine",
        "gihyo.jp": "技術評論社",
        "xtech.nikkei.com": "日経クロステック",
        "weekly.ascii.jp": "週刊アスキー",
        "toyokeizai.net": "東洋経済オンライン",
        "diamond.jp": "ダイヤモンド・オンライン",
        "thebridge.jp": "THE BRIDGE",
        "sbbit.jp": "SB Creative",
        "ainow.ai": "AINOW",
        "developers.cyberagent.co.jp": "CyberAgent",
        "techblog.yahoo.co.jp": "Yahoo! JAPAN Tech Blog",
        "developer.hatenastaff.com": "Hatena Developer Blog",
        "blog.recruit.co.jp": "Recruit Tech Blog",
        "qiita.com": "Qiita",
        "zenn.dev": "Zenn",
        "osaka-u.ac.jp": "大阪大学",
        "srad.jp": "スラド",
        "zdnet.com": "ZDNet Japan",
    }
    
    for domain, name in source_mapping.items():
        if domain in url:
            return name
    
    return "その他"


def fetch_ai_news(limit: int = NEWS_LIMIT) -> list[dict]:
    """
    日本語フィードから"AI"関連記事のタイトル＋リンクを取得し、
    limit 件だけ返す。
    """
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
            # 通常のRSS/AtomフィードをXMLで処理
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

    # AI関連キーワードでフィルタリング（拡張キーワード）
    ai_keywords = [
        "ai", "ＡＩ", "人工知能", "機械学習", "マシンラーニング", "深層学習", "ディープラーニング",
        "chatgpt", "チャットgpt", "claude", "gemini", "copilot", "gpt", "llm", "生成ai", "生成ＡＩ",
        "画像生成", "自然言語処理", "nlp", "自動化", "ロボット", "アルゴリズム", "neural",
        "tensorflow", "pytorch", "openai", "google ai", "microsoft ai", "anthropic",
        "自動運転", "音声認識", "顔認識", "予測モデル", "データサイエンス", "ビッグデータ"
    ]
    
    filtered = []
    for article in articles:
        title_lower = article["title"].lower()
        if any(keyword in title_lower for keyword in ai_keywords):
            filtered.append(article)

    # 重複排除とスコアリング
    seen_urls = set()
    seen_titles = set()
    unique = []
    
    # AIキーワードの重要度でソート
    def calculate_ai_score(title):
        title_lower = title.lower()
        score = 0
        # 重要なキーワードに高いスコア
        high_priority = ["chatgpt", "gpt", "openai", "claude", "gemini", "生成ai", "生成ＡＩ"]
        medium_priority = ["ai", "ＡＩ", "人工知能", "機械学習", "深層学習"]
        
        for keyword in high_priority:
            if keyword in title_lower:
                score += 3
        for keyword in medium_priority:
            if keyword in title_lower:
                score += 1
        return score
    
    # スコア順にソート
    filtered.sort(key=lambda x: calculate_ai_score(x["title"]), reverse=True)
    
    for article in filtered:
        # URL重複チェック
        if article["link"] in seen_urls:
            continue
        
        # タイトル類似性チェック（簡易版：最初の30文字で判定）
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
    """
    ChatWorkへメッセージ投稿。
    """
    url = f"https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/messages"
    headers = {
        "X-ChatWorkToken": CHATWORK_TOKEN,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"body": message}
    resp = requests.post(url, headers=headers, data=data)
    resp.raise_for_status()


def build_news_message(articles: list[dict]) -> str:
    """
    AIニュース一覧の統合メッセージを作成。
    """
    current_date = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M")
    
    # 情報源の統計
    sources = {}
    for article in articles:
        source = article.get("source", "不明")
        sources[source] = sources.get(source, 0) + 1
    
    # ヘッダー部分
    message_parts = [
        f"[info][title]🤖 本日のAIニュース - {current_date}[/title]",
        f"📅 配信時刻: {current_time}",
        f"📊 記事数: {len(articles)}件",
        f"📡 情報源: {len(sources)}サイト",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ""
    ]
    
    # 記事リスト部分
    for i, article in enumerate(articles, 1):
        # タイトルの長さ制限
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
    
    # 情報源サマリー（上位5つまで表示）
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
    
    # フッター部分
    message_parts.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "✨ 最新のAI情報をお届けしました！",
        "📱 気になる記事があればリンクをクリックしてご覧ください。",
        "[/info]"
    ])
    
    return "\n".join(message_parts)


def build_no_news_message() -> str:
    """
    記事が見つからない場合のメッセージを作成。
    """
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
    """
    エラー発生時のメッセージを作成。
    """
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

        # 統合メッセージを作成して投稿
        unified_msg = build_news_message(news_list)
        post_to_chatwork(unified_msg)
        
        logging.info(f"AIニュース {len(news_list)}件を一括投稿しました。")
        
    except Exception as e:
        logging.exception("スクリプト実行中にエラーが発生しました。")
        # エラー発生時の通知メッセージ
        error_msg = build_error_message()
        try:
            post_to_chatwork(error_msg)
        except:
            logging.error("エラー通知の投稿にも失敗しました。")


if __name__ == "__main__":
    main()
