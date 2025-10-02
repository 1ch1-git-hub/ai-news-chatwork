# AI News ChatWork Bot

毎日朝9時に最新のAI関連ニュースをChatWorkに自動投稿するPythonスクリプトです。

## 機能

- 日本語の主要IT・技術系メディアからAI関連記事を収集
- 記事の重複排除とスコアリング
- ChatWorkへの見やすい形式での投稿
- GitHub Actionsによる自動実行

## セットアップ

### 1. 環境変数設定
GitHubリポジトリのSettings > Secrets and variables > Actionsで以下を設定：

- `CHATWORK_TOKEN`: ChatWorkのAPIトークン
- `CHATWORK_ROOM_ID`: 投稿先のルームID

### 2. 実行スケジュール
毎日UTC 0:00 (JST 9:00)に自動実行されます。

### 3. 手動実行
ActionsタブからRun workflowで手動実行も可能です。

## 対象メディア

- Google ニュース、Yahoo! ニュース
- ITmedia、CNET Japan、ASCII.jp
- Impress Watch系、GIGAZINE
- 技術系メディア（Publickey、CodeZine等）
- 企業テックブログ（CyberAgent、Yahoo等）
- その他20+サイト

## ローカル実行

```bash
export CHATWORK_TOKEN="your_token"
export CHATWORK_ROOM_ID="your_room_id"
python chatworks.py
```

## 🔧 改善された機能詳細

### 重複排除アルゴリズム
- **URL重複チェック**: 同一記事の完全排除
- **類似コンテンツ検出**: タイトル正規化と類似度判定（80%閾値）
- **ソース分散制御**: 1つのメディアから最大1/3まで制限

### スコアリングシステム
- **Tier品質ボーナス**: 技術専門メディア重視（Tier4: +4点）
- **キーワード重み付け**: 最新AI用語（ChatGPT、生成AI等: +8点）
- **バランス調整**: 多様な観点からの情報収集を保証

### 対応キーワード（2024年版）
- **生成AI**: ChatGPT、Claude、Gemini、生成AI、LLM
- **技術**: マルチモーダル、RAG、ファインチューニング
- **ビジネス**: AI活用、DX、AI戦略、AI導入
- **新領域**: 量子AI、Edge AI、AI倫理、AI規制

## 📊 期待される改善効果

1. **重複記事の大幅削減**: 高精度な類似度判定により同内容記事を排除
2. **情報源の多様化**: 30+メディアから偏りなく選出
3. **品質向上**: Tierシステムによる信頼できるソース優先
4. **最新トレンド対応**: 2024年AI業界の最新キーワードを網羅
5. **読みやすさ向上**: ソース分散状況の可視化で透明性確保

