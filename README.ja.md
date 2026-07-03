# kids-points-v2 🌟

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SQLite](https://img.shields.io/badge/storage-SQLite-green.svg)](https://www.sqlite.org/)

> **保護者と AI が子どものポイント記録を手伝うツール。**
> 会計ソフトでも打卡アプリでもなく、自然言語で子どもが「一つ一つの進歩」を見届けられるシステムです。

**🌐 言語**: [中文](README.md) · [English](README.en.md) · **日本語**

---

## 💡 このツールが生まれた理由

多くの親が直面する小さな問題: 子どもが日々こなすタスク(書き取り・計算・打卡…)はポイントを獲得できず、課題以上のことをしても認識されません。長い間そうすると、子どもの「自律性」がルーティンに摩耗されていきます。

このシステムはその解決策を最も自然なインターフェース(Feishu グループメッセージまたは CLI ワンライナー)で提供します。保護者は子どもの**差分貢献**(追加読書、進んで机を片付け、家事の手伝い)を記録でき、子どもが「要求より良いことをした」と実感できるようにします。

### デザイン哲学: タスクではなく「差分」

| コンセプト | 意味 | ポイント |
|------|------|------|
| **日常の課業** | 算数の計算、漢字の書き取り、英語打卡 | ❌ 0ポイント(やるべきこと) |
| **差分貢献** | 課外読書、進んで机を片付ける、家事を補助 | ✅ +1 ~ +15 ポイント |
| **連続打卡** | 7/14/30日連続で課題以上を達成 | 🏆 +10 / +25 / +70 ポイント |

> **タスク(やるべきこと)= ポイントなし | 差分貢献(課題以上)= ポイントあり | 中断は補填も罰則もなし**

ポイントは週末の零食や週末活動に交換できるほか、「今日1冊本を選ぶ券」「お父さん30分付き合う券」のような無形の報酬にも交換できます。

**核心的なゴールは「ポイントを貯める」ことではなく、子どもが課題以上の行動の後に、「要求より良いことをした」と実感できるようにすることです。**

---

## ✨ kids-points-v2 とは

kids-points-v2 はこのポイントシステムの **V2 リライト版**です。V1 のキーワードマッチングから LLM セマンティック分析へ、テキストファイルから SQLite へ、単機ツールから Feishu Bot やハードウェアダッシュボードと連携できる完全なプロダクトへと進化しました。

### なぜ V2 にリライトしたのか

| 次元 | V1 | **V2** |
|------|----|--------|
| 記帳方式 | キーワードマッチング(ルール固定) | **LLM セマンティック理解**(「今日数学+1ポイント」でも「子ども今日はよくできました」でもOK) |
| データ保存 | テキストファイル(並発でデータ損失) | **SQLite**(トランザクション、停電でもデータ無傷) |
| インタラクション | スクリプト呼び出しのみ | **CLI インターフェース** + Feishu Bot |
| 音声認識 | 内蔵 ASR(重い) | **Feishu 音声文字起こしを転用**(軽い) |
| 拡張性 | なし | **ハードウェアダッシュボード、Web フロントエンド、マルチエンド連携** |

---

## 🎯 使い方

### 一番自然な使い方: Feishu グループで @bot

```
@Bot  子どもは今日進んで机を片付け、お母さんの皿洗いも手伝った
→ ✅ 記録完了: 机の片付け +1、家事補助 +1、合計 +2 ポイント

@Bot  今何ポイント？
→ 📊 現在ポイント: 77、今日変化: +2
```

### CLI 使い方(Agent / スクリプト / ハードウェア)

```bash
# 完全なパイプライン(LLM 認識 + 記帳)
python3 runtime/cli.py "子ども今日数学+1ポイント"

# 残高照会(LLM なし)
python3 runtime/cli.py balance

# 今日の明細
python3 runtime/cli.py today

# 履歴
python3 runtime/cli.py history
```

終了コード: `0` 成功 / `1` データベースエラー / `2` 引数エラー

> ⚠️ `cli.py` にメッセージ引数を渡すと **実際にデータベースに書き込みます**。ドライランではありません。

---

## 🏗️ アーキテクチャ概要

```
Feishu メッセージ
  ↓
OpenClaw skill dispatch (handle_feishu_message)
  ↓ subprocess
V2 runtime (cli.py → pipeline.py)
  ├─ LLM セマンティック分析(「誰が何をして何ポイント増」を識別)
  ├─ 重複防止(messageId ベース)
  ├─ SQLite 書き込み(data/kids_points.db)
  └─ リプライ生成 → Feishu
```

**役割分担**:
- **Agent (LLM)**: 上流の自然言語ルーティング(プラットフォーム層)
- **kids-points-v2 skill**: 確定的な記帳 + 重複防止 + データ永続化
- **SQLite**: 唯一のデータソース

---

## 🚀 クイックスタート

### クローン

```bash
git clone https://github.com/cowboy231/kids-points-v2.git
cd kids-points-v2
```

### LLM 設定

```bash
cp runtime/config.yaml.example runtime/config.yaml
# config.yaml を編集して LLM 情を報を入力
```

`key_source` は環境変数の利用を推奨します。例: `env:OPENAI_API_KEY`。

### 実行

```bash
# 残高照会
python3 runtime/cli.py balance

# 1 件記録
python3 runtime/cli.py "子ども今日数学+1ポイント"
```

### ClawHub からインストール(推奨)

```bash
clawhub install kids-points-v2
```

インストール後は skill 内に埋め込まれた runtime をデフォルトで使用。すぐ使えます。

### カスタム runtime パス(発展)

```bash
export KIDS_POINTS_RUNTIME_DIR=/path/to/your/kids-points-runtime
```

優先度: `KIDS_POINTS_RUNTIME_DIR` 環境変数 > skill 同梱の `runtime/` デフォルト

---

## 📁 ファイル構成

```
kids-points-v2/
├── README.md                    # ← あなたはここにいます(中文)
├── README.en.md                 # English version
├── README.ja.md                 # ← 日本語版(このファイル)
├── LICENSE                      # MIT
├── runtime/                     # V2 Python runtime
│   ├── cli.py                   # CLI エントリ
│   ├── db.py                    # SQLite ラッパー
│   ├── pipeline.py              # 8 ステップ記帳パイプライン
│   ├── llm_config.py            # LLM 設定レイジーローダー
│   ├── config.yaml.example      # 設定テンプレート
│   └── data/                    # SQLite 元帳の置き場(.gitignore)
├── extensions/
│   └── dashboard/               # 📺 デスクトップポイントダッシュボード(ESP32 + LED)
├── tests/                       # テストスイート(60 ユニット + golden + e2e)
└── reports/                     # テストレポート
```

---

## 🔌 依存関係

| 依存 | 説明 |
|------|------|
| Python 3.8+ | runtime 基礎 |
| OpenClaw | メッセージ分発(skill 層) |
| LLM API | OpenAI Chat Completions 互換プロトコル |
| SQLite | 標準ライブラリ、追加インストール不要 |

---

## 📐 デザイン原則

1. **データの真実性**: ポイントデータを捏造しない、すべての操作は実際の SQLite を通す
2. **関心の分離**: LLM はセマンティック理解のみ、コードがデータ操作を担当
3. **追跡可能性**: すべての取引は `data/kids_points.db` に記録、手動でクエリ可能
4. **移植性**: 標準的な OpenAI Chat Completions プロトコル、モデル交換してもビジネスロジックは無修訂
5. **自律志向**: やるべきことではなく、課題以上を報酬

---

## 🏺 プロジェクトストーリー(タイムライン)

| 時間 | マイルストーン |
|------|--------|
| 2026-05 | V1 リリース、キーワードマッチング + テキストファイル記帳 |
| 2026-06 | ルールが硬直的と発覚、方言・口語表現の識別失敗 |
| 2026-06-10 | V2 リライト決断: LLM セマンティック + SQLite |
| 2026-06-11 | V2 動作確認 + ESP32 LED ダッシュボード初版 |
| 2026-06-19 | V4.9 + dashboard in-memory cache |
| 2026-06-25 | テスト体系リリース(60 ユニット + golden + e2e) |
| 2026-07 | GitHub + ClawHub でオープンソース公開 |

---

## 🏺 関連プロジェクト

- **デスクトップポイントダッシュボード**: `extensions/dashboard/` — ESP32-WROOM-32 制御 HUB75E 全彩 RGB 128×96 LED マトリクスディスプレイ

  ![デスクトップダッシュボード実機写真](extensions/dashboard/docs/dashboard-real-hardware.jpg)

  > *全栈 100% Hermes Agent により構築——server から ESP32 ファームウェアまで。自分でデスクトップポイントボードを作りたいなら、AI agent にこのコードとハードウェア demo を参考させて、自分で完成させることができます。*
- **kids-points V1**: [clawhub.ai/cowboy231/skills/kids-points](https://clawhub.ai/cowboy231/skills/kids-points)

---

## ブランチ戦略

| ブランチ | 内容 | 用途 |
|------|------|------|
| **main** | オープンソース安全版(`config.yaml.example` + プロダクトコード) | GitHub メインブランチ、ClawHub リリース |
| **dev** | 個人使用版(実際の設定 + 内部資料 + テストデータ) | ローカル開発、プッシュしない |

---

## 📄 ライセンス

MIT © [WangYang](https://github.com/cowboy231)

---

_一つ一つの進歩を心に込めて記録する。_ 🌟
