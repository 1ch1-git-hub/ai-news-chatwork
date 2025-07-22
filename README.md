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

