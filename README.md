# kids-points-v2 🌟

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SQLite](https://img.shields.io/badge/storage-SQLite-green.svg)](https://www.sqlite.org/)

> **一个家长 + AI 给孩子记积分的工具。**
> 不是记账软件，不是打卡 App——是一套用自然语言帮孩子看见"每一点进步"的系统。

**🌐 语言 / Languages / 言語**: **中文** · [English](README.en.md) · [日本語](README.ja.md)

---

## 💡 这件事的初衷

很多家长都会遇到一个真实的小问题：孩子每天要做的事（抄写、口算、打卡……）做了不加分，而超额做了也没什么反馈。久而久之，孩子的"自驱力"被"按部就班"磨掉了。

这套系统就是想用最自然的方式（飞书群聊一句话 / CLI 一行命令），让家长能把孩子的**增量贡献**——多读一本书、主动整理书桌、帮做家务——记下来，**让孩子看见自己做了比要求更好的事**。

### 设计哲学：增量，不是任务

| 概念 | 含义 | 积分 |
|------|------|------|
| **日常课业** | 数学口算、语文抄写、英语打卡 | ❌ 0 分（份内事） |
| **增量贡献** | 课外阅读、主动整理书桌、帮做家务 | ✅ +1 ~ +15 分 |
| **连续打卡** | 连续 7/14/30 天超额完成 | 🏆 +10 / +25 / +70 分 |

> **任务（份内事）= 无积分 ｜ 增量贡献（超额）= 有积分 ｜ 中断不补不罚**

积分可以兑换周末零食、周末活动；也可以兑换非物质奖励——一张"今天选一本书"券、一张"爸爸陪玩 30 分钟"券。

**核心目标不是"攒分"，而是让孩子在每一次超额行动后，感受到"我做了一件比要求更好的事"。**

---

## ✨ kids-points-v2 是什么

kids-points-v2 是这套积分系统的 **V2 重构版**——从 V1 的关键词匹配升级到 LLM 语义分析，从文本文件升级到 SQLite，从单机工具变成可对接飞书 Bot、硬件看板的完整产品。

### 为什么重写 V2

| 维度 | V1 | **V2** |
|------|----|--------|
| 记账方式 | 关键词匹配（规则写死） | **LLM 语义理解**（"今天数学加 1 分"也行，"孩子今天表现很好"也行） |
| 数据存储 | 文本文件（并发易丢） | **SQLite**（事务、断电不丢） |
| 交互方式 | 只能脚本调 | **CLI 接口** + 飞书 Bot |
| 语音识别 | 内置 ASR（重） | **复用飞书转语音**（轻） |
| 扩展性 | 无 | **硬件看板、Web 前端、多端协同** |

---

## 🎯 怎么用它

### 最自然的用法：飞书群聊 @bot

```
@Bot  孩子今天主动整理了书桌，还帮妈妈刷了碗
→ ✅ 已记：主动整理书桌 +1，家务协助 +1，合计 +2 分

@Bot  现在多少分？
→ 📊 当前余额：77 分，今日变化：+2
```

### CLI 用法（Agent / 脚本 / 硬件）

```bash
# 走完整 pipeline（LLM 识别 + 记账）
python3 runtime/cli.py "孩子今天数学加 1 分"

# 查余额（不走 LLM）
python3 runtime/cli.py balance

# 今日明细
python3 runtime/cli.py today

# 历史记录
python3 runtime/cli.py history
```

退出码：`0` 成功 / `1` 数据库错误 / `2` 参数错误。

> ⚠️ `cli.py` 配合消息参数 = 真实写库。不是 dry-run。

---

## 🏗️ 架构概览

```
飞书消息
  ↓
OpenClaw skill dispatch (handle_feishu_message)
  ↓ subprocess
V2 runtime (cli.py → pipeline.py)
  ├─ LLM 语义分析（识别"谁做了什么加多少分"）
  ├─ 防重复（基于 messageId）
  ├─ SQLite 写库（data/kids_points.db）
  └─ 构造 reply → 飞书
```

**职责分工**：
- **Agent (LLM)**：上游自然语言路由（平台层）
- **kids-points-v2 skill**：确定性记账 + 防重复 + 数据持久化
- **SQLite**：唯一数据源

---

## 🚀 快速开始

### 克隆

```bash
git clone https://github.com/cowboy231/kids-points-v2.git
cd kids-points-v2
```

### 配置 LLM

```bash
cp runtime/config.yaml.example runtime/config.yaml
# 编辑 config.yaml，填入你的 LLM 信息
```

`key_source` 推荐用环境变量引用，例如 `env:OPENAI_API_KEY`。

### 跑起来

```bash
# 查余额
python3 runtime/cli.py balance

# 记一笔
python3 runtime/cli.py "孩子今天数学加 1 分"
```

### ClawHub 安装（推荐）

```bash
clawhub install kids-points-v2
```

安装后默认用 skill 内嵌的 runtime，开箱即用。

### 自定义 runtime 路径（高级）

```bash
export KIDS_POINTS_RUNTIME_DIR=/path/to/your/kids-points-runtime
```

优先级：`KIDS_POINTS_RUNTIME_DIR` env > skill 内嵌 `runtime/` 默认值。

---

## 📁 文件结构

```
kids-points-v2/
├── README.md                    # ← 你在这里（中文）
├── README.en.md                 # English
├── README.ja.md                 # 日本語
├── LICENSE                      # MIT
├── runtime/                     # V2 Python runtime
│   ├── cli.py                   # CLI 入口
│   ├── db.py                    # SQLite 封装
│   ├── pipeline.py              # 8 步记账 pipeline
│   ├── llm_config.py            # LLM 配置懒加载
│   ├── config.yaml.example      # 配置模板
│   └── data/                    # SQLite 账本位置（.gitignore）
├── extensions/
│   └── dashboard/               # 📺 桌面积分看板（ESP32 + LED）
├── tests/                       # 测试套件（60 单元 + golden + e2e）
└── reports/                     # 测试报告
```

---

## 🔌 依赖

| 依赖 | 说明 |
|------|------|
| Python 3.8+ | runtime 基础 |
| OpenClaw | 消息分发（skill 层） |
| LLM API | OpenAI Chat Completions 兼容协议 |
| SQLite | 标准库，无需额外安装 |

---

## 📐 设计原则

1. **数据真实**：积分数据绝不编造，每次操作走真实 SQLite
2. **职责分离**：LLM 只负责语义理解，代码负责数据操作
3. **可追溯**：所有交易记录在 `data/kids_points.db`，可手动查询
4. **可移植**：标准 OpenAI Chat Completions 协议，换模型不改业务逻辑
5. **自驱导向**：奖励增量贡献，不奖励份内事

---

## 🏺 项目故事（时间线）

| 时间 | 里程碑 |
|------|--------|
| 2026-05 | V1 上线，关键词匹配 + 文本文件记账 |
| 2026-06 | 发现规则不够灵活，方言/口语化表达识别失败 |
| 2026-06-10 | 决策重写 V2：LLM 语义 + SQLite |
| 2026-06-11 | V2 跑通 + ESP32 LED 看板第一版 |
| 2026-06-19 | V4.9 + dashboard in-memory cache |
| 2026-06-25 | 测试体系上线（60 单元 + golden + e2e） |
| 2026-07 | 开源到 GitHub + ClawHub |

---

## 🏺 配套项目

- **桌面积分看板**：`extensions/dashboard/` — ESP32 + LED 矩阵屏的桌面版展示
- **kids-points V1**：[clawhub.ai/cowboy231/skills/kids-points](https://clawhub.ai/cowboy231/skills/kids-points)

---

## 分支策略

| 分支 | 内容 | 用途 |
|------|------|------|
| **main** | 开源安全版（`config.yaml.example` + 产品代码） | GitHub 主分支、ClawHub 发布 |
| **dev** | 自用版（真实配置 + 内部资料 + 测试数据） | 本地开发，不推送 |

---

## 📄 License

MIT © [老王](https://github.com/cowboy231)

---

_用心记录每一次进步。_ 🌟