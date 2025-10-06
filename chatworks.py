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
NEWS_LIMIT       = 8  # 🔥 改善: マルチカテゴリー対応で8件に増加（AI 4件 + その他 4件）

# 設定チェック
if not CHATWORK_TOKEN or not CHATWORK_ROOM_ID:
    logging.error("環境変数 CHATWORK_TOKEN と CHATWORK_ROOM_ID を設定してください")
    sys.exit(1)

# 🔥 改善: マルチカテゴリー対応の高品質ニュースソース
# カテゴリー: AI, OFFICE, CISCO, BUSINESS, SELF_DEV
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

# 🆕 追加カテゴリー用のフィード（Office/Excel、Cisco、ビジネススキル、自己啓発）
ADDITIONAL_FEEDS = {
    # Microsoft Office・Excel関連
    "office": [
        "https://www.microsoft.com/en-us/microsoft-365/blog/feed/",
        "https://office-hack.com/feed/",  # Office系日本語ブログ
        "https://www.moug.net/rss.xml",   # Excel・Access技術情報
    ],
    
    # Cisco・ネットワーク関連
    "cisco": [
        "https://blogs.cisco.com/rss",
        "https://www.cisco.com/c/en/us/about/press/news-rss.xml",
        "https://network.gihyo.jp/feed/rss2",  # ネットワーク技術日本語
        "https://atmarkit.itmedia.co.jp/rss/rdf/ait.rdf",  # @IT ネットワーク
    ],
    
    # ビジネス・自己啓発関連
    "business_skills": [
        "https://diamond.jp/list/feed/rss",
        "https://toyokeizai.net/list/feed/rss",
        "https://www.lifehacker.jp/feed/index.xml",
        "https://studyhacker.net/feed",  # 学習効率化
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
    """URLから情報源の名前を取得（マルチカテゴリー対応版）"""
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
        # Office/Excel関連
        "techcommunity.microsoft.com": "Microsoft Tech",
        "support.microsoft.com": "Microsoft Support",
        "microsoft.com": "Microsoft",
        "office-hack.com": "Office Hack",
        "moug.net": "MOUG",
        # Cisco/ネットワーク関連  
        "blogs.cisco.com": "Cisco Blogs",
        "learningnetwork.cisco.com": "Cisco Learning",
        "cisco.com": "Cisco",
        "network.gihyo.jp": "ネットワーク技評",
        "atmarkit.itmedia.co.jp": "@IT",
        # ビジネス・自己啓発関連
        "president.jp": "PRESIDENT",
        "newspicks.com": "NewsPicks",
        "lifehacker.jp": "ライフハッカー",
        "studyhacker.net": "STUDY HACKER",
        "globis.jp": "グロービス",
    }
    
    for domain, name in source_mapping.items():
        if domain in url:
            return name
    return "その他"

def get_article_category(title: str) -> str:
    """記事タイトルからカテゴリーを判定"""
    title_lower = title.lower()
    
    # カテゴリー別キーワード辞書
    category_keywords = {
        "ai": [
            # AI基本キーワード
            "ai", "ＡＩ", "人工知能", "機械学習", "深層学習", "ディープラーニング",
            # 生成AI・LLM
            "生成ai", "生成ＡＩ", "大規模言語モデル", "llm", "生成型ai", "ジェネレーティブai",
            # 主要AIサービス
            "chatgpt", "チャットgpt", "gpt", "claude", "gemini", "bard", "copilot",
            "mistral", "llama", "palm", "dall-e", "midjourney", "stable diffusion",
        ],
        
        "office": [
            # Microsoft Office関連
            "excel", "エクセル", "microsoft office", "office 365", "microsoft 365", "microsoft",
            "word", "ワード", "powerpoint", "パワーポイント", "パワポ",
            "outlook", "アウトルック", "access", "アクセス",
            "onenote", "ワンノート", "teams", "チームズ",
            # Excel機能関連
            "vlookup", "pivot", "ピボット", "関数", "マクロ", "vba", "スプレッドシート",
            "ショートカット", "便利機能", "効率化", "自動化", "表計算",
            # 広く業務効率化関連
            "業務効率", "生産性", "テレワーク", "リモートワーク", "デジタル化",
        ],
        
        "cisco": [
            # Cisco関連
            "cisco", "シスコ", "ccna", "ccnp", "ccie", "ccent",
            "routing", "switching", "ルーティング", "スイッチング",
            # ネットワーク関連
            "network", "ネットワーク", "tcp/ip", "bgp", "ospf", "eigrp",
            "vlan", "stp", "vpn", "セキュリティ", "サイバー",
            "インフラ", "サーバー", "スイッチ", "ルーター", "クラウド",
            # 技術系キーワード
            "システム", "it", "エンジニア", "クラウドコンピューティング", "aws", "azure",
        ],
        
        "business_skills": [
            # ビジネススキル関連
            "空雨傘", "空・雨・傘", "事実・解釈・打手",
            "ロジカルシンキング", "問題解決", "思考法", "論理的",
            "マネジメント", "リーダーシップ", "コミュニケーション", "管理",
            "プレゼンテーション", "会議", "交渉", "営業", "プレゼン",
            # ビジネスフレームワーク
            "mece", "3c", "4p", "swot", "pdca", "kpi", "okr",
            "戦略", "マーケティング", "ブランディング", "経営", "事業",
            # ビジネス一般
            "ビジネス", "企業", "会社", "経済", "投資", "財務", "会計",
            "キャリア", "転職", "働き方", "組織", "チーム", "人材",
        ],
        
        "self_development": [
            # 7つの習慣関連
            "7つの習慣", "七つの習慣", "スティーブン・コヴィー",
            "主体性", "終わりを思い描く", "最優先事項",
            "win-win", "理解してから理解される", "シナジー",
            # アドラー心理学関連
            "アドラー", "アドラー心理学", "個人心理学",
            "勇気", "共同体感覚", "課題の分離", "目的論",
            # 自己啓発一般
            "自己啓発", "スキルアップ", "成長", "学習", "勉強", "教育",
            "モチベーション", "習慣", "目標設定", "時間管理", "集中力",
            "ライフハック", "生産性", "効率化", "ワークライフバランス",
            # 健康・メンタル
            "健康", "メンタル", "ストレス", "睡眠", "運動", "心理", "マインド",
            "幸福", "充実", "バランス", "リフレッシュ", "コツ", "方法",
        ]
    }
    
    # スコアリング: キーワードマッチ数でカテゴリーを判定
    category_scores = {}
    for category, keywords in category_keywords.items():
        score = sum(1 for keyword in keywords if keyword in title_lower)
        if score > 0:
            category_scores[category] = score
    
    if not category_scores:
        return "other"
    
    # 最高スコアのカテゴリーを返す
    return max(category_scores.items(), key=lambda x: x[1])[0]

def fetch_multi_category_news(limit: int = NEWS_LIMIT) -> list[dict]:
    """マルチカテゴリー記事を取得（AI + ビジネススキル + 技術系）"""
    articles = []
    successful_feeds = 0
    failed_feeds = 0
    source_stats = {}  # ソース別記事数統計
    
    # 全てのTierからフィードを取得
    all_feeds = []
    for tier_name, feeds in FEED_URLS.items():
        for url in feeds:
            all_feeds.append((url, tier_name, "ai_source"))
    
    # ADDITIONAL_FEEDSも追加
    for category_name, feeds in ADDITIONAL_FEEDS.items():
        for url in feeds:
            all_feeds.append((url, category_name, "additional_source"))
    
    logging.info(f"処理対象フィード数: {len(all_feeds)}件")
    
    for url, category_or_tier, feed_type in all_feeds:
        try:
            logging.info(f"Fetching feed: {url} (Category/Tier: {category_or_tier}, Type: {feed_type})")
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
                        # 記事のカテゴリーを判定
                        article_category = get_article_category(title)
                        
                        articles.append({
                            "title": title,
                            "link": link,
                            "source": source_name,
                            "tier": category_or_tier if feed_type == "ai_source" else "additional",
                            "category": article_category,
                            "feed_type": feed_type
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
                        # 記事のカテゴリーを判定
                        article_category = get_article_category(title)
                        
                        articles.append({
                            "title": title,
                            "link": link,
                            "source": source_name,
                            "tier": category_or_tier if feed_type == "ai_source" else "additional",
                            "category": article_category,
                            "feed_type": feed_type
                        })
                        source_stats[source_name] += 1
                        
        except Exception as e:
            logging.warning(f"フィード解析失敗 ({get_source_name(url)}): {e}")
    
    # ソース統計をログ出力
    logging.info(f"取得した全記事数: {len(articles)}件")
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
    
    # 🔥 改善: マルチカテゴリーフィルタリング
    # 全ての記事を残す（"other"も含む）でカテゴリーバランスを向上
    filtered = articles

    # 🔥 改善: バランス重視のマルチカテゴリースコアリング機能
    category_counts = {}  # カテゴリー別の選択済み記事数を追跡
    
    def calculate_multi_category_score(article):
        title_lower = article["title"].lower()
        source = article.get("source", "")
        tier = article.get("tier", "additional")
        category = article.get("category", "other")
        score = 0
        
        # バランシングボーナス: 少ないカテゴリーの記事に大きなボーナス
        current_count = category_counts.get(category, 0)
        balance_bonus = max(0, 10 - (current_count * 3))  # 同じカテゴリーが多いほどスコア減少
        score += balance_bonus
        
        # Tierボーナス（AIソースのみ）
        if tier != "additional":
            tier_bonus = {
                "tier1": 2, "tier2": 3, "tier3": 2,
                "tier4": 4, "tier5": 1, "tier6": 1
            }
            score += tier_bonus.get(tier, 1)
        else:
            score += 3  # 追加ソースのベーススコアを上げる
        
        # カテゴリー別ボーナス（バランス重視）
        category_bonus = {
            "ai": 3,              # AIの優先度を下げる
            "office": 5,          # Officeスキルの優先度を上げる
            "cisco": 4,           # 技術系の優先度を上げる
            "business_skills": 5, # ビジネススキルの優先度を上げる
            "self_development": 5, # 自己啓発の優先度を上げる
            "other": 2            # その他も考慮に入れる
        }
        score += category_bonus.get(category, 1)
        
        # カテゴリー別キーワード重み付け
        if category == "ai":
            ultra_keywords = ["chatgpt", "claude", "gemini", "生成ai"]
            high_keywords = ["openai", "llm", "大規模言語モデル"]
            for kw in ultra_keywords:
                if kw in title_lower: score += 4  # スコアを下げる
            for kw in high_keywords:
                if kw in title_lower: score += 2  # スコアを下げる
                
        elif category == "office":
            key_keywords = ["excel", "powerpoint", "エクセル", "ショートカット", "vba", "microsoft"]
            for kw in key_keywords:
                if kw in title_lower: score += 8  # スコアを上げる
                
        elif category in ["business_skills", "self_development"]:
            popular_keywords = ["空雨傘", "7つの習慣", "アドラー", "ロジカル", "ビジネス", "経営"]
            for kw in popular_keywords:
                if kw in title_lower: score += 7
        
        elif category == "cisco":
            tech_keywords = ["cisco", "ネットワーク", "システム", "クラウド", "サーバー"]
            for kw in tech_keywords:
                if kw in title_lower: score += 6
        
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
    filtered.sort(key=calculate_multi_category_score, reverse=True)
    
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
        
        # カテゴリー別カウントを更新
        category = article.get("category", "other")
        category_counts[category] = category_counts.get(category, 0) + 1
        
        if len(unique) >= limit:
            break

    # 🆕 カテゴリーバランシング: 各カテゴリーから最低1件は含めるように調整
    if len(unique) < limit:
        category_counts = {}
        for article in unique:
            category = article.get("category", "other")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 不足しているカテゴリーから記事を追加
        target_categories = ["ai", "office", "cisco", "business_skills", "self_development"]
        for target_category in target_categories:
            if category_counts.get(target_category, 0) == 0 and len(unique) < limit:
                # このカテゴリーの記事を探して追加
                for article in filtered:
                    if (article.get("category") == target_category and 
                        article["link"] not in seen_urls and
                        len(unique) < limit):
                        
                        unique.append(article)
                        seen_urls.add(article["link"])
                        category_counts[target_category] = 1
                        break

    # 結果統計をログ出力
    final_source_stats = {}
    final_category_stats = {}
    for article in unique:
        source = article.get("source", "不明")
        category = article.get("category", "other")
        final_source_stats[source] = final_source_stats.get(source, 0) + 1
        final_category_stats[category] = final_category_stats.get(category, 0) + 1
    
    logging.info(f"Selected {len(unique)} articles from {len(filtered)} filtered articles")
    logging.info(f"最終選択ソース分散: {dict(sorted(final_source_stats.items(), key=lambda x: x[1], reverse=True))}")
    logging.info(f"最終カテゴリー分散: {dict(sorted(final_category_stats.items(), key=lambda x: x[1], reverse=True))}")
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
    """マルチカテゴリーニュース一覧メッセージを作成"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M")
    
    # ソース統計、カテゴリー統計、Tier情報を集計
    sources = {}
    category_stats = {}
    tier_stats = {}
    
    for article in articles:
        source = article.get("source", "不明")
        category = article.get("category", "other")
        tier = article.get("tier", "additional")
        
        sources[source] = sources.get(source, 0) + 1
        category_stats[category] = category_stats.get(category, 0) + 1
        tier_stats[tier] = tier_stats.get(tier, 0) + 1
    
    message_parts = [
        f"[info][title]🚀 週間ビジネススキルダイジェスト - {current_date}[/title]",
        f"📅 配信時刻: {current_time} (毎週月曜日配信)",
        f"📊 記事数: {len(articles)}件 (厳選・重複排除済)",
        f"📡 情報源: {len(sources)}サイト (バランス調整済)",
        f"🏷️ カテゴリー: {len(category_stats)}種類 (AI・ビジネススキル・技術)",
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
        
        # カテゴリーごとのアイコン
        category_icons = {
            'ai': '🤖',              # AI関連
            'office': '📈',          # Office/Excel
            'cisco': '🌐',           # Cisco/ネットワーク
            'business_skills': '💼', # ビジネススキル
            'self_development': '🌱'  # 自己啓発
        }
        category = article.get('category', 'other')
        category_icon = category_icons.get(category, '📰')
        
        message_parts.extend([
            f"{category_icon} 【記事 {i}】{source} ({category.upper()})",
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
            "🏷️ カテゴリ別分散:"
        ])
        
        category_names = {
            'ai': '🤖 AI・機械学習',
            'office': '📈 Office・Excelスキル', 
            'cisco': '🌐 Cisco・ネットワーク',
            'business_skills': '💼 ビジネススキル',
            'self_development': '🌱 自己啓発・成長'
        }
        
        for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            category_name = category_names.get(category, f'❓ {category}')
            message_parts.append(f"　• {category_name}: {count}件")
        
        message_parts.append("")
    
    message_parts.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "✨ 高品質・多様な情報源から厳選したビジネススキル情報をお届け！",
        "🔍 重複排除・ソース分散アルゴリズムにより品質を確保。",
        "📱 気になる記事があればリンクをクリックしてご覧ください。",
        "📅 次回配信: 来週月曜日の朝9時です。",
        "💡 AI・Office・Cisco・ビジネススキル・自己啓発の5カテゴリーを網羅。",
        "[/info]"
    ])
    
    return "\n".join(message_parts)

def build_no_news_message() -> str:
    """記事が見つからない場合のメッセージ"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M")
    
    return (
        f"[info][title]🚀 本日のビジネススキルニュース - {current_date}[/title]\n"
        f"📅 配信時刻: {current_time}\n"
        f"📊 記事数: 0件\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 申し訳ございません。本日は新しい関連記事が見つかりませんでした。\n"
        f"📰 来週また最新情報をお届けいたします！\n\n"
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
        f"🚨 ビジネススキルニュース配信でエラーが発生しました。\n"
        f"🔧 システム管理者にご確認ください。\n"
        f"🕐 次回の配信をお待ちください。\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"[/info]"
    )

def main():
    try:
        news_list = fetch_multi_category_news()
        
        if not news_list:
            logging.warning("取得できた記事がありませんでした。")
            no_news_msg = build_no_news_message()
            post_to_chatwork(no_news_msg)
            return

        unified_msg = build_news_message(news_list)
        post_to_chatwork(unified_msg)
        
        logging.info(f"マルチカテゴリーニュース {len(news_list)}件を一括投稿しました。")
        
    except Exception as e:
        logging.exception("スクリプト実行中にエラーが発生しました。")
        error_msg = build_error_message()
        try:
            post_to_chatwork(error_msg)
        except:
            logging.error("エラー通知の投稿にも失敗しました。")

if __name__ == "__main__":
    main()
