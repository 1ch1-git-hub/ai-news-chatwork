#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
test_news_fetch.py - ニュース取得機能のテストスクリプト
ChatWorkに投稿せず、記事取得のみをテストする
"""

import sys
sys.path.append('.')

from chatworks import fetch_multi_category_news, build_news_message, build_no_news_message
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def test_news_fetch():
    """記事取得のテスト"""
    print("=" * 60)
    print("🔍 ニュース取得機能テスト開始")
    print("=" * 60)
    
    try:
        # 記事取得テスト
        print("\n📰 記事取得中...")
        news_list = fetch_multi_category_news()
        
        print(f"\n✅ 取得結果: {len(news_list)}件の記事を取得")
        
        if news_list:
            # カテゴリー別統計
            category_stats = {}
            for article in news_list:
                category = article.get('category', 'other')
                category_stats[category] = category_stats.get(category, 0) + 1
            
            print("\n📊 カテゴリー別統計:")
            for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {category}: {count}件")
            
            print("\n📝 取得した記事の例 (最初の5件):")
            for i, article in enumerate(news_list[:5], 1):
                print(f"  {i}. [{article.get('category', 'other').upper()}] {article['title'][:60]}...")
                print(f"     ソース: {article.get('source', '不明')}")
                print()
            
            # メッセージ生成テスト
            print("🔄 ChatWorkメッセージ生成テスト...")
            message = build_news_message(news_list)
            
            # メッセージの最初の部分を表示（長いので一部のみ）
            lines = message.split('\n')
            print("\n📄 生成されたメッセージ（最初の15行）:")
            for line in lines[:15]:
                print(f"  {line}")
            print(f"  ... (全{len(lines)}行)")
            
        else:
            print("⚠️ 記事が見つかりませんでした")
            message = build_no_news_message()
            print("\n📄 「記事なし」メッセージ:")
            print(message)
        
        print("\n" + "=" * 60)
        print("✅ テスト完了")
        print("=" * 60)
        
        return len(news_list) > 0
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        logging.exception("テスト中にエラーが発生")
        return False

if __name__ == "__main__":
    success = test_news_fetch()
    sys.exit(0 if success else 1)