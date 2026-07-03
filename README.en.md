# kids-points-v2 🌟

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SQLite](https://img.shields.io/badge/storage-SQLite-green.svg)](https://www.sqlite.org/)

> **A parent + AI tool for tracking kids' points.**
> Not accounting software, not a check-in app — it's a system that uses natural language to help children see "every bit of progress."

**🌐 Languages**: [中文](README.md) · **English** · [日本語](README.ja.md)

---

## 💡 Why This Exists

Many parents run into the same small problem: kids do their daily tasks (copying, drills, check-ins...) without earning anything, and going the extra mile gets no recognition either. Over time, a child's self-drive gets worn down by routine.

This system tries to solve that with the most natural interface — a Feishu group message or a CLI one-liner — so parents can log their kid's **incremental contributions** (an extra book, proactively tidying up, helping with housework) and let the child see that they did something better than required.

### Design Philosophy: Increments, Not Tasks

| Concept | Meaning | Points |
|------|------|------|
| **Daily schoolwork** | Math drills, Chinese copying, English check-ins | ❌ 0 points (within duties) |
| **Incremental contributions** | Extra reading, proactively tidying desk, helping with housework | ✅ +1 ~ +15 points |
| **Consecutive check-ins** | 7/14/30 consecutive days of going beyond | 🏆 +10 / +25 / +70 points |

> **Tasks (within duties) = no points | Incremental contributions (going beyond) = points | No make-up, no penalty for breaks**

Points can be redeemed for weekend snacks, weekend activities; or non-material rewards — a "pick a book today" voucher, a "dad plays with you for 30 minutes" voucher.

**The core goal isn't "saving up points," but letting the child feel, after every extra action, that "I did something better than required."**

---

## ✨ What is kids-points-v2

kids-points-v2 is the **V2 rewrite** of this point system — upgrading from V1's keyword matching to LLM semantic analysis, from text files to SQLite, from a single-machine tool to a complete product that integrates with Feishu Bot and hardware dashboards.

### Why Rewrite to V2

| Dimension | V1 | **V2** |
|------|----|--------|
| Accounting method | Keyword matching (rigid rules) | **LLM semantic understanding** (works for "1 point for math today" or "the kid behaved well today") |
| Data storage | Text files (loss-prone under concurrency) | **SQLite** (transactions, survives power loss) |
| Interaction | Script calls only | **CLI interface** + Feishu Bot |
| Speech recognition | Built-in ASR (heavy) | **Reuse Feishu voice-to-text** (lightweight) |
| Extensibility | None | **Hardware dashboards, web frontend, multi-end coordination** |

---

## 🎯 How To Use It

### Most Natural Way: @bot in Feishu Group

```
@Bot  The kid proactively tidied their desk today and helped mom wash the dishes
→ ✅ Recorded: tidied desk +1, housework help +1, total +2 points

@Bot  What's the current balance?
→ 📊 Current balance: 77 points, today's change: +2
```

### CLI Usage (Agent / Scripts / Hardware)

```bash
# Full pipeline (LLM recognition + accounting)
python3 runtime/cli.py "the kid gets 1 point for math today"

# Check balance (no LLM needed)
python3 runtime/cli.py balance

# Today's details
python3 runtime/cli.py today

# History
python3 runtime/cli.py history
```

Exit codes: `0` success / `1` database error / `2` argument error.

> ⚠️ `cli.py` with a message argument **actually writes to the database**. Not a dry-run.

---

## 🏗️ Architecture Overview

```
Feishu message
  ↓
OpenClaw skill dispatch (handle_feishu_message)
  ↓ subprocess
V2 runtime (cli.py → pipeline.py)
  ├─ LLM semantic analysis (recognize "who did what for how many points")
  ├─ Duplicate prevention (based on messageId)
  ├─ SQLite write (data/kids_points.db)
  └─ Build reply → Feishu
```

**Responsibility split**:
- **Agent (LLM)**: Upstream natural language routing (platform layer)
- **kids-points-v2 skill**: Deterministic accounting + duplicate prevention + data persistence
- **SQLite**: Single source of truth

---

## 🚀 Quick Start

### Clone

```bash
git clone https://github.com/cowboy231/kids-points-v2.git
cd kids-points-v2
```

### Configure LLM

```bash
cp runtime/config.yaml.example runtime/config.yaml
# Edit config.yaml and fill in your LLM information
```

`key_source` recommends using environment variables, e.g. `env:OPENAI_API_KEY`.

### Run

```bash
# Check balance
python3 runtime/cli.py balance

# Record a transaction
python3 runtime/cli.py "the kid gets 1 point for math today"
```

### Install via ClawHub (Recommended)

```bash
clawhub install kids-points-v2
```

After install, the skill uses its embedded runtime by default — works out of the box.

### Custom Runtime Path (Advanced)

```bash
export KIDS_POINTS_RUNTIME_DIR=/path/to/your/kids-points-runtime
```

Priority: `KIDS_POINTS_RUNTIME_DIR` env > skill's embedded `runtime/` default.

---

## 📁 File Structure

```
kids-points-v2/
├── README.md                    # ← You are here (Chinese)
├── README.en.md                 # English version
├── README.ja.md                 # 日本語版
├── LICENSE                      # MIT
├── runtime/                     # V2 Python runtime
│   ├── cli.py                   # CLI entry
│   ├── db.py                    # SQLite wrapper
│   ├── pipeline.py              # 8-step accounting pipeline
│   ├── llm_config.py            # LLM config lazy loader
│   ├── config.yaml.example      # Config template
│   └── data/                    # SQLite ledger location (.gitignore)
├── extensions/
│   └── dashboard/               # 📺 Desktop points dashboard (ESP32 + LED)
├── tests/                       # Test suite (60 unit + golden + e2e)
└── reports/                     # Test reports
```

---

## 🔌 Dependencies

| Dependency | Description |
|------|------|
| Python 3.8+ | runtime foundation |
| OpenClaw | Message dispatch (skill layer) |
| LLM API | OpenAI Chat Completions compatible protocol |
| SQLite | Standard library, no extra install |

---

## 📐 Design Principles

1. **Real data**: Never fabricate point data, every operation goes through real SQLite
2. **Separation of concerns**: LLM only does semantic understanding, code handles data operations
3. **Traceability**: All transactions in `data/kids_points.db`, queryable by hand
4. **Portability**: Standard OpenAI Chat Completions protocol, switch models without changing business logic
5. **Self-drive orientation**: Reward incremental contributions, not duties

---

## 🏺 Project Story (Timeline)

| Date | Milestone |
|------|--------|
| 2026-05 | V1 launched, keyword matching + text file accounting |
| 2026-06 | Found rules too rigid, dialect/colloquial expressions failed |
| 2026-06-10 | Decided to rewrite V2: LLM semantic + SQLite |
| 2026-06-11 | V2 working + ESP32 LED dashboard v1 |
| 2026-06-19 | V4.9 + dashboard in-memory cache |
| 2026-06-25 | Test system online (60 unit + golden + e2e) |
| 2026-07 | Open source on GitHub + ClawHub |

---

## 🏺 Related Projects

- **Desktop Points Dashboard**: `extensions/dashboard/` — ESP32 + LED matrix display, desktop version
- **kids-points V1**: [clawhub.ai/cowboy231/skills/kids-points](https://clawhub.ai/cowboy231/skills/kids-points)

---

## Branch Strategy

| Branch | Content | Use |
|------|------|------|
| **main** | Open-source safe version (`config.yaml.example` + product code) | GitHub main branch, ClawHub release |
| **dev** | Personal version (real config + internal docs + test data) | Local development, not pushed |

---

## 📄 License

MIT © [WangYang](https://github.com/cowboy231)

---

_Recording every bit of progress with care._ 🌟
