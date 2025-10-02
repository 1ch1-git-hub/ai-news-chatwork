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

# 🔥 改善: 多様で高品質なニュースソース（品質・バランス重視）
FEED_URLS = {
    # Tier 1: 主要総合ニュース（基本情報収集）
    "tier1": [
        "https://news.google.com/rss/search?q=AI+OR+人工知能+OR+機械学習&hl=ja&gl=JP&ceid=JP:ja",
        "https://news.yahoo.co.jp/rss/topics/it.xml",
        "https://www3.nhk.or.jp/rss/news/cat06.xml",  # NHK 科学・文化
    ],
    
    # Tier 2: IT専門メディア（技術詳細）
    "tier2": [
        "https://rss.itmedia.co.jp/rss/2.0/itmedia_aiplus.xml",
        "https://rss.itmedia.co.jp/rss/2.0/itmedia_news.xml",
        "https://japan.cnet.com/rss/index.rdf",
        "https://ascii.jp/rss.xml",
        "https://www.watch.impress.co.jp/data/rss/1.0/ipw/feed.rdf",
    ],
    
    # Tier 3: ビジネス・分析系（戦略・市場視点）
    "tier3": [
        "https://www.nikkei.com/rss/",
        "https://toyokeizai.net/list/feed/rss",
        "https://diamond.jp/list/feed/rss",
        "https://newswitch.jp/rss/index.rdf",
    ],
    
    # Tier 4: 技術専門・開発者向け（深い技術情報）
    "tier4": [
        "https://www.publickey1.jp/atom.xml",
        "https://xtech.nikkei.com/rss/index.rdf",
        "https://gihyo.jp/feed/rss2",
        "https://codezine.jp/rss/new/20/index.xml",
        "https://ainow.ai/feed/",
    ],
    
    # Tier 5: 開発コミュニティ（実践・トレンド）
    "tier5": [
        "https://qiita.com/popular-items/feed",
        "https://zenn.dev/feed",
        "https://note.com/rss",
    ],
    
    # Tier 6: 企業テックブログ（実装例・事例）
    "tier6": [
        "https://developers.cyberagent.co.jp/blog/feed/",
        "https://techblog.yahoo.co.jp/atom.xml",
        "https://engineering.mercari.com/blog/feed.xml",
        "https://developer.hatenastaff.com/rss",
    ]
}

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
    """URLから情報源の名前を取得（拡張版）"""
    source_mapping = {
        "news.google.com": "Google ニュース",
        "news.yahoo.co.jp": "Yahoo! ニュース",
        "www3.nhk.or.jp": "NHK",
        "itmedia.co.jp": "ITmedia",
        "japan.cnet.com": "CNET Japan",
        "ascii.jp": "ASCII.jp",
        "watch.impress.co.jp": "Impress Watch",
        "www.nikkei.com": "日本経済新聞",
        "toyokeizai.net": "東洋経済",
        "diamond.jp": "ダイヤモンド",
        "newswitch.jp": "ニュースイッチ",
        "publickey1.jp": "Publickey",
        "xtech.nikkei.com": "日経クロステック",
        "gihyo.jp": "技術評論社",
        "codezine.jp": "CodeZine",
        "ainow.ai": "AINOW",
        "qiita.com": "Qiita",
        "zenn.dev": "Zenn",
        "note.com": "note",
        "developers.cyberagent.co.jp": "CyberAgent",
        "techblog.yahoo.co.jp": "Yahoo! JAPAN",
        "engineering.mercari.com": "メルカリ",
        "developer.hatenastaff.com": "はてな",
    }
    
    for domain, name in source_mapping.items():
        if domain in url:
            return name
    return "その他"

def fetch_ai_news(limit: int = NEWS_LIMIT) -> list[dict]:
    """AI関連記事を取得（ソース分散確保機能付き）"""
    articles = []
    successful_feeds = 0
    failed_feeds = 0
    source_stats = {}  # ソース別記事数統計
    
    # 全てのTierからフィードを取得
    all_feeds = []
    for tier_name, feeds in FEED_URLS.items():
        for url in feeds:
            all_feeds.append((url, tier_name))
    
    for url, tier in all_feeds:
        try:
            logging.info(f"Fetching feed: {url} (Tier: {tier})")
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
            
            # ソース別統計を初期化
            if source_name not in source_stats:
                source_stats[source_name] = 0
            
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
                            "source": source_name,
                            "tier": tier
                        })
                        source_stats[source_name] += 1
            
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
                            "source": source_name,
                            "tier": tier
                        })
                        source_stats[source_name] += 1
                        
        except Exception as e:
            logging.warning(f"フィード解析失敗 ({get_source_name(url)}): {e}")
    
    # ソース統計をログ出力
    logging.info(f"ソース別記事数: {dict(sorted(source_stats.items(), key=lambda x: x[1], reverse=True))}")

    logging.info(f"フィード取得結果: 成功 {successful_feeds}件, 失敗 {failed_feeds}件")

    # 🔥 改善: 包括的で最新のAIキーワード（2024年トレンド対応）
    ai_keywords = [
        # 基本キーワード（必須）
        "ai", "ＡＩ", "人工知能", "機械学習", "深層学習", "ディープラーニング",
        
        # 生成AI・LLMトレンド（高優先度）
        "生成ai", "生成ＡＩ", "大規模言語モデル", "llm", "生成型ai", "ジェネレーティブai",
        
        # 主要AIサービス・モデル
        "chatgpt", "チャットgpt", "gpt", "claude", "gemini", "bard", "copilot",
        "mistral", "llama", "palm", "dall-e", "midjourney", "stable diffusion",
        
        # 企業・技術プラットフォーム
        "openai", "anthropic", "google ai", "microsoft ai", "meta ai",
        "transformer", "diffusion", "neural network", "ニューラルネット",
        
        # 応用分野・技術
        "画像生成", "aiライティング", "自動化", "チャットボット", "音声ai",
        "コード生成", "翻訳ai", "要約ai", "検索ai", "推薦システム",
        
        # ビジネス・産業応用
        "ai活用", "dxai", "aiソリューション", "ai導入", "ai戦略",
        "自動運転", "医療ai", "金融ai", "教育ai", "農業ai",
        
        # 最新トレンド（2024年）
        "マルチモーダル", "rag", "ファインチューニング", "プロンプト", "エージェント",
        "ai倫理", "ai規制", "explainable ai", "edge ai", "量子ai"
    ]
    
    filtered = []
    for article in articles:
        title_lower = article["title"].lower()
        if any(keyword in title_lower for keyword in ai_keywords):
            filtered.append(article)

    # 🔥 改善: 精密なスコアリング機能（Tier考慮、キーワード重み付け）
    def calculate_ai_score(article):
        title_lower = article["title"].lower()
        source = article.get("source", "")
        tier = article.get("tier", "tier6")
        score = 0
        
        # Tierボーナス（高品質ソース優先）
        tier_bonus = {
            "tier1": 2,  # 総合ニュース
            "tier2": 3,  # IT専門メディア
            "tier3": 2,  # ビジネス系
            "tier4": 4,  # 技術専門
            "tier5": 1,  # コミュニティ
            "tier6": 1   # 企業ブログ
        }
        score += tier_bonus.get(tier, 1)
        
        # 最高優先度キーワード（2024年トレンド）
        ultra_priority = ["chatgpt", "gpt-4", "claude", "gemini", "生成ai", "マルチモーダル"]
        high_priority = ["openai", "anthropic", "大規模言語モデル", "llm", "copilot", "dall-e"]
        medium_priority = ["ai", "ＡＩ", "人工知能", "機械学習", "自動化", "チャットボット"]
        
        for keyword in ultra_priority:
            if keyword in title_lower:
                score += 8
        for keyword in high_priority:
            if keyword in title_lower:
                score += 5
        for keyword in medium_priority:
            if keyword in title_lower:
                score += 2
        
        return score
    
    # 🔥 改善: 強化された重複排除アルゴリズム
    import re
    from difflib import SequenceMatcher
    
    def normalize_title(title):
        """ タイトルを正規化して比較しやすくする """
        # 特殊文字、句読点、数字を除去
        normalized = re.sub(r'[\u3000-\u303f\uff01-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff65]', '', title)
        normalized = re.sub(r'[0-9０-９]+', '', normalized)  # 数字を除去
        normalized = re.sub(r'\s+', '', normalized)  # スペースを除去
        return normalized.lower().strip()
    
    def is_similar_content(title1, title2, threshold=0.8):
        """ タイトルの似た内容を検出 """
        norm1 = normalize_title(title1)
        norm2 = normalize_title(title2)
        
        if len(norm1) < 10 or len(norm2) < 10:
            return norm1 == norm2
        
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= threshold
    
    # 重複排除とスコア順ソート（ソース分散考慮）
    seen_urls = set()
    seen_normalized_titles = []  # 正規化されたタイトルのリスト
    unique = []
    source_count = {}  # ソース別記事数カウント
    
    # スコア順でソート
    filtered.sort(key=calculate_ai_score, reverse=True)
    
    for article in filtered:
        # URL重複チェック
        if article["link"] in seen_urls:
            continue
        
        # タイトルの似た内容重複チェック
        current_title = article["title"]
        is_duplicate = False
        for seen_title in seen_normalized_titles:
            if is_similar_content(current_title, seen_title):
                is_duplicate = True
                break
        
        if is_duplicate:
            continue
        
        # ソース分散チェック（同じソースからの記事が多すぎないか）
        source_name = article.get("source", "不明")
        current_source_count = source_count.get(source_name, 0)
        max_per_source = max(1, limit // 3)  # 一つのソースからの最大記事数
        
        if current_source_count >= max_per_source:
            # このソースからは十分記事を取得したのでスキップ
            continue
        
        # 記事を追加
        seen_urls.add(article["link"])
        seen_normalized_titles.append(current_title)
        unique.append(article)
        source_count[source_name] = current_source_count + 1
        
        if len(unique) >= limit:
            break

    # 結果統計をログ出力
    final_source_stats = {}
    for article in unique:
        source = article.get("source", "不明")
        final_source_stats[source] = final_source_stats.get(source, 0) + 1
    
    logging.info(f"Selected {len(unique)} AI articles from {len(filtered)} filtered articles")
    logging.info(f"最終選択ソース分散: {dict(sorted(final_source_stats.items(), key=lambda x: x[1], reverse=True))}")
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
    """AIニュース一覧メッセージを作成（改善版）"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M")
    
    # ソース統計とTier情報を集計
    sources = {}
    tier_stats = {}
    for article in articles:
        source = article.get("source", "不明")
        tier = article.get("tier", "tier6")
        sources[source] = sources.get(source, 0) + 1
        tier_stats[tier] = tier_stats.get(tier, 0) + 1
    
    message_parts = [
        f"[info][title]🤖 週間AIニュースダイジェスト - {current_date}[/title]",
        f"📅 配信時刻: {current_time} (毎週月曜日配信)",
        f"📊 記事数: {len(articles)}件 (厳選・重複排除済)",
        f"📡 情報源: {len(sources)}サイト (バランス調整済)",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ""
    ]
    
    for i, article in enumerate(articles, 1):
        title = article['title']
        if len(title) > 80:
            title = title[:77] + "..."
        
        source = article.get('source', '不明')
        tier = article.get('tier', 'tier6')
        
        # Tierごとのアイコン
        tier_icons = {
            'tier1': '📢',  # 総合ニュース
            'tier2': '💻',  # IT専門
            'tier3': '💼',  # ビジネス
            'tier4': '⚙️',   # 技術専門
            'tier5': '👥',  # コミュニティ
            'tier6': '🏢'   # 企業
        }
        tier_icon = tier_icons.get(tier, '📰')
        
        message_parts.extend([
            f"{tier_icon} 【記事 {i}】{source}",
            f"💡 {title}",
            f"🔗 {article['link']}",
            ""
        ])
    
    # ソース分散情報を表示
    if len(sources) > 1:
        message_parts.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📈 情報源分散状況 (重複排除・バランス調整済):",
            ""
        ])
        
        sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
        for source, count in sorted_sources:
            message_parts.append(f"　• {source}: {count}件")
        
        message_parts.extend([
            "",
            "🔍 カテゴリ別分散:"
        ])
        
        tier_names = {
            'tier1': '総合ニュース',
            'tier2': 'IT専門メディア', 
            'tier3': 'ビジネス系',
            'tier4': '技術専門',
            'tier5': 'コミュニティ',
            'tier6': '企業ブログ'
        }
        
        for tier, count in sorted(tier_stats.items()):
            tier_name = tier_names.get(tier, tier)
            message_parts.append(f"　• {tier_name}: {count}件")
        
        message_parts.append("")
    
    message_parts.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "✨ 高品質・多様な情報源から厳選したAIニュースをお届け！",
        "🔍 重複排除・ソース分散アルゴリズムにより品質を確保。",
        "📱 気になる記事があればリンクをクリックしてご覧ください。",
        "📅 次回配信: 来週月曜日の朝9時です。",
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
