# 儿童积分看板 — 完整设计文档 (v0.3)

> 本文件是 M0.5 阶段的"完整设计" — 范围收窄后, 端到端描述清楚每个组件的输入/输出/责任.
> 老王要拍板的事都在 `notes.md` (🟡 可答不阻塞 M1).
> 任务拆解在 `kanban.md`.
>
> **v0.7 changelog (2026-06-25)**:
> - **M1.2 server WS-on-connect 增强** (v5.4.1): `server.py` `ws_handler` 在 client 连入后立即推 1 次 `{"type": "refresh", "reason": "ws_connect"}`. 修正 v5.4 "启动时推 1 次" 的旧行为 — server 启动时 `ws_clients` 还是空集, 那次 broadcast 等于白推; 新 client 连入时拿不到 "初始数据就绪" 信号. 验证 3 项全过: 单 client / 2 client 并发 / inotify 推.
> - **本轮 (2026-06-25) 实测状态**: M1.1 ✅ M1.2 ✅ M1.3 ✅ M1.4 ✅ M1.5 📋 (end-to-end + systemd 落地). server 当前手动跑 (pid 737160 后 systemd 化), watchdog alive, /api/dashboard 返 total_balance=39.5 / 5 行流水 / today_count=0.
>
> **v0.6 changelog (2026-06-15)**:
> - **M1.3 v1.1 完成 + 本地编译验证通过**: `code/esp32/desktop/desktop.ino` (398 行, 改 desktop-dashboard.ino → desktop.ino 跟 arduino-cli 编译要求一致).
> - **M1.4 ✅ 完成 (2026-06-19)**: ¥190 板到货 + 烧录调通 + 4 区 dashboard 渲染. 关键: 店家伙 v2.0.7 库 (默认 pinmap R1=14/E=16) 替代自装 v3.0.14 (默认 R1=25/E=-1 错配), 100% 复刻店家 HUB75E.txt, 字号 1-255 全支持, 双缓冲 + 5s 周期刷 (99.96% 静态). 备份: `desktop.ino.v2.3_M14_baseline`. 沉到 skill: `home-dashboard-display` Pitfall #33-#48 (24+ fill_test 失败根因 + 店家库 vs 自装库 + HUB75E B2 脚位 = E + v3 字段速查). **M1.5 候选** (老王 06-19 建议): "完全推模式" — server 推整帧 JSON → ESP32 直接 render, 0 主动拉 + 0 周期刷 = 0 撕裂闪烁. 留作"未来升级", 不阻塞 M1 收尾.
>   - **#2 字号**: 标题 `setTextSize(2)` (10×14 物理像素, 装 18 物理高标题区), 流水/底栏 `setTextSize(1)` (5×7 物理像素) — 对齐 sim 36/24/20 屏像素
>   - **#1 中文**: 加 `U8g2_for_Adafruit_GFX` 桥接, 用 `u8g2_font_unifont_t_chinese1` (12×13 像素, ~14KB Flash, ~1000 CJK chars). 渲染时分流: 纯 ASCII 走 GFX 5x7, 含中文走 U8g2 chinese1 + UTF-8 截断 6 字
>   - **#3 密码**: `TODO_FILL_PASSWORD` → D17 实际值 `YOUR_WIFI_PASSWORD` (memory 标 [REDACTED] 是为不写进 git history, 实际值在 .ino, M1.4 老王再 double check 1 次)
> - **Arduino 环境配齐**: `arduino-cli 1.5.1` 装到 `~/.local/bin/`, ESP32 平台 `2.0.17` (跟 ESPAsyncWebServer 3.1.0 + mbedtls 兼容, 3.3.10 跟 ESPAsyncWebServer 有 breaking change), 6 个库全装 (HUB75 3.0.14 / ArduinoJson 7.4.3 / ESPAsyncWebServer 3.1.0 / AsyncTCP 1.1.4 / U8g2 2.36.19 / U8g2_for_Adafruit_GFX 1.8.0).
> - **编译验证**: `arduino-cli compile --fqbn esp32:esp32:esp32 .` ✅ 0 错误 0 警告. Flash 1033729 bytes (78%) / RAM 52360 bytes (15%). 实测可烧.
> - **M1.3 仍留 v1.2 (不阻塞)**: #4 NTP 时间同步 (M3 候选, 暂不实现).
> - **M1.3 修复 v1.1 路上踩的坑** (沉到 `home-dashboard-display` skill): 1) ESP32 平台 3.x 跟 ESPAsyncWebServer 3.1.0 双重不兼容 (mbedtls API + pxCurrentTCB), 走 2.0.17 才稳; 2) HUB75 v3 库头文件改名 `ESP32-HUB75-MatrixPanel-DMA.h` → `ESP32-HUB75-MatrixPanel-I2S-DMA.h`; 3) HUB75_I2S_CFG 构造器第 4 参数是 `i2s_pins` struct 不是 int; 4) arduino-cli 编译期待主文件跟目录同名 (`desktop.ino` not `desktop-dashboard.ino`); 5) esptool 4.5+ 需要 pyserial (`pip install pyserial`).
>
> **v0.5 changelog (2026-06-15)**:
> - **M1.3 ESP32 main.ino 完成**: `code/esp32/desktop/desktop-dashboard.ino` (365 行) + `code/esp32/desktop/README.md` (107 行). HUB75 (mrcodetastic/ESP32-HUB75-MatrixPanel-DMA) + WiFi + 30s 拉 (D21) + WS `/ws` 收 refresh 立即拉 + 4 区渲染 (跟 sim 横版 1:1 物理 y) + 关蓝 B=0 (D4) + ArduinoOTA + Wi-Fi 自动重连 + 4 调试接口 (/health /refresh /setup?brightness /ws). **编译验证待 M1.4 烧录时 Arduino IDE** (本机无 arduino-cli). 详见 § 5 ESP32 实现 + § 9 M1.3 ✅.
> - v1 已知限制 (M1.3 之后迭代, 不阻塞 M1.4 烧录):
>   1. 中文 description 显示为 `[zh N]` 占位 (v1.1 加 u8g2 12x12 中文字体, ~10KB Flash)
>   2. 字号 5x7 GFX 物理 1px 偏小 (v1.1 改 setTextSize 2/1/1 对齐 sim 36/24/20 屏像素)
>   3. Wi-Fi 密码硬编码 (v1.1 加 WiFiManager 配网页, 免重烧)
>   4. 无 NTP 时间同步 (v1.1 加 NTPClient 显示"最近更新: 12:30")
>
> **v0.4 changelog (2026-06-15)**:
> - **M1.1 持久化**: `desktop_sim.py` 顶部新增 `ORIENTATION_CONFIGS` 字典 (横 128×96 / 竖 96×128) + `set_orientation()` 函数, `tune.py --orientation {horizontal,vertical}` 切换. 2 套布局在 § 5 已分小节, 仿真已跑通 (PNG 存在 `/tmp/sim_tune_{horizontal,vertical}_*.png`). 详见 § 5 横/竖 2 子节 + § 9 M1.1 ✅.
> - **M1.2 Python server 完成**: `code/server/data_source.py` (V2 CLI 包装层) + `code/server/server.py` (Flask + flask-sock WS + watchdog inotify V2 SQLite, **v5.4 in-memory cache 模式 + WS 广播 refresh**). systemd 单元 `code/server/dashboard.service` 待 M1.5 落地 (本轮无 sudo, 仅手动跑验证).
>   - `curl http://localhost:8080/api/dashboard` 返有效 JSON (含 total_balance / today / recent[5])
>   - `curl http://localhost:8080/health` 返 `{"ok": true, ...watchdog_alive...}`
>   - WS `/ws`: 启动时推 1 次, V2 DB 变化 (inotify) 推 refresh
>   - `curl -X POST http://localhost:8080/api/push` 手动标 dirty + WS 广播
>
> **v0.3 changelog (2026-06-14)**:
> - **数据源切 V2**: 从 V1 `balance.json` 切到 **kids-points V2 SQLite** (`kids-points-runtime/data/kids_points.db`), 通过 V2 CLI 包装层调数据
> - V1 永不动硬约束**保持** — 本项目只读 V2 不动 V1, 跟 kids-points 硬约束兼容 ✅
> - **3 个 CLI 接口** + 数据格式定版 (balance / today / history), 详见 § 3
> - 同步机制: inotify 监听 V2 SQLite 文件 (替代 V1 balance.json), 频率 5min → 30s (V2 promotion 前 DB 不增长, 频率可降)
> - 跟 kids-points 06-14 09:30 拍板的 MVP dashboard CLI 路径对齐

---

## 1. 范围与目标

### 业务范围 (2026-06-12 收窄 → 2026-06-14 数据源更新)

- **业务只展示积分** (kids-points V2 数据只读显示, 永不录入/编辑/对账)
- 看板 = kids-points 数据的视觉呈现, 录入在 kids-points V1 飞书 agent (生产中, 永不动)
- **不动 V1** — V1 是 source of truth (kids-points 硬约束), dashboard 只读 V2 SQLite via CLI
- **数据源 = kids-points V2 SQLite**, 通过 V2 CLI 包装层调数据 (详见 § 3)

### 3 个目标

1. **桌面 dashboard 端到端跑通 (下周二 6/16 交付)** — 改 kids-points 数据 → 板立即更新
2. **挂墙屏预留** — M2+ 实施, 不阻塞 M1
3. **软件架构稳** — 双保险 (30s 拉 + WS 推), 推失败不影响主

### 范围外 (不做)

- ❌ 不做积分录入/编辑/撤销 UI
- ❌ 不动 V1 (`balance.json`, `agent-handler.js`, `input.log` 都不动)
- ❌ 不写 V2 (V2 写入走 kids-points 飞书 bot, 本项目只读)
- ❌ 不做 Web 录入页 (M7 可选)
- ❌ 不接天气/日历 (M7 可选)

---

## 2. 硬件 (沿用 M0 决策, 不变)

| 形态 | 屏数 | 单板 | 桌面对角 | 比例 | 整套价 | 状态 |
|---|---|---|---|---|---|---|
| **桌面 dashboard** (M1 主战场) | 1 | ¥190 P2 128×96 (闲鱼) | 11" 4:3 | 4:3 | **¥220-280** (板+ESP32+电源) | 已下单, 等快递 |
| 挂墙屏 (M2+, 不阻塞 M1) | 4 | P2 320×160 × 1×4 | 50" 8:1 | 8:1 横幅 | ¥800-1300 | 未开始采购 |

**M0 决策不变**:
- ✅ LED 矩阵 (非 LCD/投影/e-ink)
- ✅ ESP32-WROOM-32 + HUB75E 适配板 (非 Pi)
- ✅ DIY 单元板 (非强力巨彩 Q 系列)
- ✅ 黑底 + 琥珀 (R=255, G=140, B=0) + 关蓝通道 (B=0)
- ✅ 1 电源 + 分配板 (M2 挂墙用)
- ✅ 静态散热 (无风扇)
- ✅ HTTP 拉 (主) + **in-memory cache 模式 (v5.4 取代 WS 推备)**

---

## 3. 数据源

### Source of Truth: kids-points V2 SQLite (via CLI 包装)

```
V2 DB 路径: /home/wang/projects/kids-points-v2/runtime/data/kids_points.db
V2 CLI 路径: /home/wang/projects/kids-points-v2/runtime/cli.py
```

**V1 永不动硬约束保持** (per `kids-points` skill 硬约束, 2026-06-12 老王拍板):
- V1 (`~/.openclaw/agents/kids-study/workspace/kids-points/`) 永不动
- 本项目只读 V2 SQLite, **不写 V1, 不写 V2** (V2 写入走 kids-points 飞书 bot)

**为什么数据源从 V1 切 V2** (2026-06-14 决策, 跟 kids-points 06-14 09:30 拍板的 MVP dashboard CLI 路径对齐):
- kids-points V2 团队 (老王) 给 dashboard 留了 CLI 接口 (2026-06-14 MVP 落地)
- V2 SQLite 是结构化数据 (vs V1 自由 JSON), 未来扩展 (周报/月度) 复用 db.py helper
- 跟"V1 永不动"硬约束兼容 — 读 V2 ≠ 动 V1

### V2 CLI 3 个接口 (2026-06-14 MVP, kids-points-runtime/cli.py)

**接口 1: `balance` (当前余额)**
```bash
python3 /home/wang/桌面/龙虾工作区/StuAgent/New\ project/kids-points-runtime/cli.py balance
```
返回:
```json
{
  "balance": 2,
  "balance_display": "2",
  "as_of": "2026-06-14T09:30:47.828888",
  "source": "v2_sqlite"
}
```

**接口 2: `today` (今日积分)**
```bash
python3 /home/wang/桌面/龙虾工作区/StuAgent/New\ project/kids-points-runtime/cli.py today
```
返回:
```json
{
  "date": "2026-06-14",
  "income": 5,
  "expense": -3,
  "net": 2,
  "tx_count": 4,
  "balance": 2,
  "balance_display": "2"
}
```

**接口 3: `history` (近期历史)**
```bash
python3 /home/wang/桌面/龙虾工作区/StuAgent/New\ project/kids-points-runtime/cli.py history --days 7 --limit 50
```
返回:
```json
{
  "from": "2026-06-08",
  "to": "2026-06-14",
  "days": 7,
  "tx_count": 50,
  "history": [
    {
      "date": "2026-06-14",
      "time": "09:30:47",
      "type": "expense",
      "amount": -2,
      "description": "买冰激凌"
    }
  ]
}
```

### V2 CLI 输出字段表 (dashboard 映射用)

| V2 CLI 字段 | 类型 | 含义 | dashboard 用法 |
|---|---|---|---|
| `balance` | int | 当前余额 (V2 SQLite transactions sum) | `total_balance` |
| `balance_display` | str | 余额的字符串表示 (整数, V2 暂不接小数, V2-015 拒收浮点) | 同上 (备用) |
| `as_of` | ISO datetime | 余额快照时间 | `last_updated` |
| `source` | str | 固定 `"v2_sqlite"` | 调试/健康检查 |
| `date` (today) | YYYY-MM-DD | 今日日期 (本地 tz) | 健康检查 |
| `income` | int | 今日 income 之和 | (备, 当前未用) |
| `expense` | int | 今日 expense 之和 (负数) | (备, 当前未用) |
| `net` | int | 今日 net (income + expense) | `today_net` |
| `tx_count` (today) | int | 今日事务数 | `today_count` |
| `from` / `to` | YYYY-MM-DD | history 范围 (含 from 和 to) | 健康检查 |
| `days` | int | `--days` 参数回显 | 调试 |
| `tx_count` (history) | int | 实际返回的历史条数 (≤ `--limit`) | 健康检查 |
| `history[].date` | YYYY-MM-DD | 单条事务日期 | `recent[].date` |
| `history[].time` | HH:MM:SS | 单条事务时间 (本地 tz) | `recent[].time` (备) |
| `history[].type` | str `"income"` / `"expense"` | 收入/支出 | `recent[].type` 符号映射 |
| `history[].amount` | int (负数 for expense) | 变动量 (有符号) | `recent[].amount` (取绝对值) |
| `history[].description` | str | 事务描述 (中文, V2 LLM 抽取) | `recent[].description` |

### V2 production DB 数据稀疏是 design 行为 (重要!)

V2 production `kids_points.db` 在 **V2 promotion 接飞书之前不会增长**:
- V2 promotion 之前 (当前), V2 走 replay.py 批处理, 写在隔离 DB `runN_*.db`, **production DB 没新数据**
- MVP dashboard CLI 跑 production DB 看到 `tx_count=0` / 余额停在老数据是**正常**, 跟 V2 promotion 状态强相关, **不是 bug**
- 详细看 `kids-points` skill § "V2 production DB 数据稀疏是设计行为"

### Dashboard 读 V2 的方式 (包装层)

- 新增 `code/server/data_source.py` (V2 CLI 包装层, 详见 § 8 文件结构)
- 包装层调 `subprocess.run(["python3", "<V2 CLI 路径>", "balance"])` → 解析 JSON → 返 dict
- **不解析 V2 SQLite 文件本身** (那是 kids-points V2 团队的事), 只调 CLI
- **不调 LLM** — 3 个 CLI 接口都是纯读, 0 token, 秒级响应
- **不写 V2** — 只读 3 个接口 (`balance` / `today` / `history`), 写 (process) 不在本项目范围

### 失败兜底

- V2 CLI 调失败 (subprocess exit != 0) → 包装层抛 `DataSourceError`, server 返 HTTP 503 + 上次缓存
- V2 CLI 输出不是合法 JSON → 包装层抛 `DataSourceError`, 同上
- V2 DB 文件不存在 / 路径错 → server 启动时报错, systemd 重启
- 网络挂 (V2 CLI 在本机, 不涉及网络) → 不适用
- 完整兜底在 § 6 同步机制

---

## 4. Dashboard JSON Schema (Flask GET /api/dashboard 输出)

```json
{
  "schema_version": 1,
  "title": "KID POINTS",
  "total_balance": 108.5,
  "today_count": 5,
  "today_net": 4.0,
  "recent": [
    {
      "date": "06-11",
      "type": "+",
      "amount": 6,
      "description": "跳绳+口算",
      "balance_after": 108.5
    },
    {
      "date": "06-11",
      "type": "-",
      "amount": 5,
      "description": "吃萨莉亚",
      "balance_after": 103.5
    },
    {
      "date": "06-10",
      "type": "+",
      "amount": 3,
      "description": "ABC Reading",
      "balance_after": 108.5
    }
  ],
  "last_updated": "2026-06-11T22:22:00"
}
```

**字段说明**:

| 字段 | 来源 (V2 CLI) | 计算 |
|---|---|---|
| `title` | config (`dashboard.json` 或 env `DASHBOARD_TITLE`) | 静态可配 |
| `total_balance` | `cli.py balance` 的 `balance` 字段 | 直接取 |
| `today_count` | `cli.py today` 的 `tx_count` 字段 | 直接取 |
| `today_net` | `cli.py today` 的 `net` 字段 | 直接取 |
| `recent` | `cli.py history --days 1 --limit 3` 的 `history[]` | 取最后 3 条, 按 V2 顺序 (最新在前) |
| `last_updated` | `cli.py balance` 的 `as_of` 字段 | 直接取 |

**`type` 符号映射** (V2 CLI → dashboard):
- V2 `type == "income"` → dashboard `type == "+"`, `amount = |history[].amount|`
- V2 `type == "expense"` → dashboard `type == "-"`, `amount = |history[].amount|`

**`date` 简化**: V2 `"2026-06-14"` → dashboard `"06-14"` (节省 LED 矩阵宽度).

**`description`**: V2 CLI 返回的中文 description, dashboard 截断到 12 字符 (LED 128px 宽, 8px 字体 6px 宽, 12 字符 ≈ 72 像素), 超出滚动 (M3 可选).

**示例文件**: `code/data/balance_view.json` (本轮新加, V2 字段版).

---

## 5. 显示布局 (4 区, ¥190 P2 128×96 = 128×96 像素)

### 物理布局

```
物理: 256×192mm (11" 4:3, P2.0mm 点距)
像素: 128×96 (1/32 扫, HUB75)
```

### 屏幕分区

```
┌────────────────────────────────────────────┐  y=0
│  KID POINTS                                 │  ← 顶: 标题 (12px, 琥珀, y=4-20)
│  ─────────────────────                      │  ← 分隔线 (1px, 琥珀, y=22)
│                                            │
│  +6  06-11  跳绳+口算                       │  ← 中: 3 行最近流水
│  -5  06-11  吃萨莉亚                        │     (8px 字体, y=28-44, 44-60, 60-76)
│  +3  06-10  ABC Reading                    │
│                                            │
│  ─────────────────────                      │  ← 分隔线 (y=78)
│  今日 +4.0      总 108.5                   │  ← 底: 今日+总积分 (10px, y=82-94)
└────────────────────────────────────────────┘  y=95
```

### 竖向 (板旋转 90°, M1.1 v1.3 持久化)

```
物理: 96×128 (11" 3:4, ¥190 P2 板旋转 90° 安装, 物理像素 96 宽 × 128 高)
```

```
┌──────────────────┐  y=0
│  KID POINTS       │  ← 顶: 标题 (屏 36 = 物理 6 字符, y=4-26)
│  ────────────     │  ← 分隔线 (y=26)
│                  │
│  +6  06-11  跳绳+ │  ← 中: 3 行流水
│  -5  06-11  吃萨利 │     字号 24 (物理 4 字符 advance), y=32-56, 56-80, 80-108
│  +3  06-10  ABC  │
│                  │
│  ────────────     │  ← 分隔线 (y=108)
│  今日 +4  总 108  │  ← 底 (字号 24, y=112-128)
└──────────────────┘  y=127
```

**竖向 vs 横向差异** (M1.1 v1.3 实测选定, 写入 `code/sim/desktop_sim.py` 顶部 `ORIENTATION_CONFIGS`):

| 项 | 横向 (128×96) | 竖向 (96×128) | 差异原因 |
|---|---|---|---|
| W×H | 128×96 | 96×128 | 板旋转 90° |
| TITLE_FONT_PX | 36 | 36 | 一致 (标题醒目优先) |
| ROW_FONT_PX | 24 | 24 | 一致 (流水 20 字符完整装 96 屏宽) |
| FOOTER_FONT_PX | 20 | 24 | 竖向底栏加大 (跟行字号齐平, 视觉平衡) |
| TITLE_Y / DIVIDER_1_Y | 4 / 22 | 4 / 26 | 竖向标题区稍增, 给字号溢出留 padding |
| ROW_1/2/3_Y | 28 / 44 / 60 | 32 / 56 / 80 | 竖向行高 24 物理 (比横 16 大 50%), 字号对应增 |
| DIVIDER_2_Y / FOOTER_Y | 78 / 82 | 108 / 112 | 竖向底栏 16 物理高 (比横 12 大) |

**切换方法** (M1.1 v1.3 持久化):
- **仿真**: `tune.py --orientation vertical` (横/竖一键切, 不改 `desktop_sim.py`); 默认 horizontal
- **代码内**: `from desktop_sim import set_orientation; set_orientation("vertical")` → 改 sim 全局常量
- **选定后写回**: 改 `desktop_sim.py` 顶部 `ORIENTATION_CONFIGS` 2 个 dict + `DEFAULT_ORIENTATION` 常量 (方式 B 持久)
- **硬件**: ESP32 C++ 端同理, 启动时根据板安装方向设 1 个 const (M1.3 实施)

**竖向容量核算**:
- 96 屏宽, ROW_FONT_PX=24 advance ≈ 4 物理像素, 24 字符完整装下 (流水实际最大 20 字符)
- 3 行流水 × 24 物理行高 = 72 物理 (ROW_1_Y=32 到 ROW_3_Y+字号溢出≈108, 全在 0-128 屏内)
- 底栏 FOOTER_FONT_PX=24, "今日 +4  总 108" 12 字符 ≈ 48 物理像素, 装 96 屏宽 OK

### 字体与颜色

| 元素 | 字体 (像素) | 颜色 (R,G,B) | 关蓝 |
|---|---|---|---|
| 标题 | 12px (bdf 或 GFX) | 琥珀 (255, 140, 0) | B=0 |
| 流水行 | 8px | 琥珀 (255, 140, 0) | B=0 |
| 分隔线 | 1px | 琥珀 (255, 140, 0) | B=0 |
| 底栏 (今日/总) | 10px | 琥珀 (255, 140, 0) | B=0 |
| 背景 | - | 黑 (0, 0, 0) | - |

**夜间模式** (M3 可选): 0:00-6:00 降到 20% 亮度, 白天 50-70% 亮度.

### 容量核算

- 8px 字符 ≈ 6px 宽 (中英文), 长行 12 字符 = 72 像素
- 128 像素宽, **放下** ✓
- 流水 description 截断到 12 字符, 超出滚动 (M3 可选)

---

## 6. 同步机制

### 主: ESP32 主动拉 + Service in-memory cache (v5.4)

```
ESP32 启动 → 连 Wi-Fi → 5 秒一次 GET /api/dashboard → 渲染
                              ↓
                        memcmp 智能渲染 (数据没变不重画)
                              ↓
                        网络断 → 用 ESP32 端 last_good RAM 缓存, 不白屏
```

**5 秒频率** (v4.8 从 30s 改 5s):
- v4.8 引入 memcmp 智能渲染后, 拉频繁无成本 (没变不重画)
- 5s 内数据变更可见 (V2 写后下次拉就看到)
- 30s 太久, 用户体验差

### 备: watchdog 监听 V2 SQLite → 标 cache dirty + WS 广播 refresh

```
V2 SQLite 文件变化 (inotify)
       ↓
   Python watchdog Observer (code/server/server.py V2DBHandler)
       ↓
   mark_cache_dirty("watchdog: ...") (微秒级, 不调 subprocess)
       ↓
   ws_broadcast({"type": "refresh"}) → 连 WS 的客户端即时收到通知
       ↓
   下次 GET /api/dashboard 触发 fetch_data() (或客户端收到 WS 后主动拉)
       ↓
   ESP32 收到新数据, memcmp 比对, 变了才重画
```

**v5.4+ 架构**:
- watchdog 标 in-memory cache dirty (微秒级, 不调 subprocess) — 99% 请求走 cache
- WS 广播 `{"type": "refresh"}` 给所有连 WS 的客户端 (ESP32 端用 AsyncWebSocket), 通知立即拉
- 双重保障: WS 连不上 → 退化到 5s 轮询 (ESP32 端兜底)
- WS 启动时推 1 次 (初始数据就绪)
- 可靠性: subprocess 调用 720/小时 → 每天几次 (V2 DB 写才触发)

**触发方式**:
- **方式 1 (默认)**: inotify 监听 V2 SQLite 文件 (`kids_points.db`) 变化 → 推
  - V2 promotion 之前 DB 不增长, inotify 永远不触发 (退化到 30s 拉)
  - V2 promotion 之后 V2 飞书 bot 写 DB → inotify 触发 → <1s 端到端推
- **方式 2 (兜底)**: 老王手动 `curl -X POST http://<server>:8080/api/push`
- **方式 3 (未来)**: kids-points 团队后续如果接 webhook, 调用我们预留的 `POST /api/push` 端点 — **注意: 本项目不实施, 只留接口**

#### 失败兜底

- **WS 推失败** (ESP32 离线) → 不影响主, ESP32 30s 后还会拉
- **HTTP 拉失败** (服务器挂 / V2 CLI 失败) → ESP32 用本地缓存渲染, 显示"离线"标记 (M3 可选)
- **V2 SQLite 损坏 / 路径错** → Python server 启动时报错, systemd 重启; 运行时损坏 → 包装层 `DataSourceError`, server 返 HTTP 503 + 上次缓存, 推 alert 通知老王 (M3 可选)
- **V2 CLI 输出非合法 JSON** → 包装层 `DataSourceError`, 同上

#### 时序图 (V2 promotion 后路径)

```
t=0      ESP32 启动, GET /api/dashboard
t=0.1s   200 OK, 渲染
t=0.2s   WS 连上服务器
t=1.0s   稳定显示, 等待
t=2.0s   老王发飞书 "数学口算+3"
t=2.5s   V2 飞书 bot (kids-points-v2) 收消息, 调 V2 pipeline 写 kids_points.db
t=2.51s  inotify 触发 (V2 SQLite 文件 mtime 变)
t=2.52s  Python data_source.py 调 V2 CLI `balance` 拿最新
t=2.53s  WS 推 {"action": "refresh"} 给所有 ESP32
t=2.6s   ESP32 收到, 立即 GET /api/dashboard
t=2.7s   200 OK, 渲染新数据
t=2.8s   板显示更新 (从 t=2.0s 到 t=2.8s, 端到端 <1s)
```

#### 时序图 (V2 promotion 前路径, 当前)

```
t=0      ESP32 启动, GET /api/dashboard
t=0.1s   200 OK, 渲染
t=0.2s   WS 连上服务器
t=1.0s   稳定显示, 等待
t=2.0s   老王发飞书 "数学口算+3"
t=2.5s   V1 飞书 bot (kids-study, 生产中) 收消息, 写 V1 balance.json
         (V2 SQLite 不变! 跟 V1 永不动硬约束兼容)
t=2.6s   (V2 promotion 前, inotify 不触发 V2 SQLite)
t=30s    ESP32 30s 拉一次, 调 V2 CLI 拿 production DB 数据
         production DB 还没增长 → 板显示旧数据
t=30.1s  200 OK, 渲染旧数据 (V2 production DB 跟 V1 余额可能不一致)

⚠️ V2 promotion 前 会出现: V1 已加, 但 V2 production DB 还没数据
   → 板显示跟 V1 余额对不上, 但这是 V2 promotion 前的**预期行为** (V2 DB 数据稀疏, design)
   → V2 promotion 后这个问题自动消失 (V2 飞书 bot 直接写 V2 DB)
```

---

## 7. 网络 & 部署

### 服务器: 这台 Linux 机器本身

- 老王已确认 Q2: "Linux服务器, 就是你这台机器本身"
- **IP**: 待老王提供 (`ip addr` 可查, 默认 LAN)
- **hostname**: `linux-2` (或 `wangmouren`) — 用 IP 更稳

### Flask 监听

- `0.0.0.0:8080` (老王这机器 LAN 内全可达)
- ESP32 端 `SERVER_URL = "http://<IP>:8080/api/dashboard"` (config 块写)

### 端口冲突检查

```bash
ss -tlnp | grep 8080   # 没占用才用 8080
```

### systemd 自启

- `/etc/systemd/system/dashboard.service` (待写, M1.5)
- 7×24 后台, 失败 3 次重启
- 日志: `journalctl -u dashboard -f`

### 老王网络环境

- 老王已确认 Q3: "密码和网络也就是你现在的网络"
- Wi-Fi SSID/密码: 待老王提供 (写在 ESP32 config 块, M1 必答)

---

## 8. 文件结构

```
/home/wang/projects/kids-points-v2/extensions/dashboard/
├── README.md                (项目说明)
├── kanban.md                (项目看板, M0.5+ 任务)
├── notes.md                 (讨论 + 决策)
├── CHECKLIST.md             (启动 checklist)
├── docs/
│   ├── plan.md              (本文件, 完整设计, v0.3)
│   └── hardware.md          (M1 验货 checklist, 待写)
├── code/
│   ├── server/
│   │   ├── server.py        (Flask + WS + inotify, M1 实施)
│   │   ├── data_source.py   (V2 CLI 包装层, 2026-06-14 新加, M1.2 实施)
│   │   └── requirements.txt
│   ├── esp32/
│   │   ├── desktop/desktop-dashboard.ino  (M1 实施, 4 区渲染, 30s 拉 + WS 收)
│   │   ├── desktop/README.md
│   │   └── wall/wall-display.ino          (M2+, 大字版)
│   └── data/
│       ├── todos.json       (旧, 通用待办, 保留为示例)
│       └── balance_view.json (V2 字段版仪表板 JSON schema 示例)
└── V2 数据路径 (只读, 跟 kids-points 硬约束兼容):
    /home/wang/桌面/龙虾工作区/StuAgent/New project/kids-points-runtime/
    ├── cli.py               (V2 CLI 入口, 3 个 dashboard 接口: balance/today/history)
    └── data/kids_points.db  (V2 production DB, dashboard 只读)

V1 路径 (永不动, 跟 kids-points 硬约束):
    ~/.openclaw/agents/kids-study/workspace/kids-points/
    (本项目 v0.3 之后不再读 V1, 保留路径仅供审计/回滚)
```

### `data_source.py` 设计 (V2 CLI 包装层)

```python
# code/server/data_source.py (伪代码, M1.2 实施)
import subprocess
import json

V2_CLI = "/home/wang/projects/kids-points-v2/runtime/cli.py"

class DataSourceError(Exception):
    pass

def get_balance() -> dict:
    """调 V2 CLI `balance` → 返 dict"""
    try:
        result = subprocess.run(
            ["python3", V2_CLI, "balance"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            raise DataSourceError(f"V2 CLI exit {result.returncode}: {result.stderr}")
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        raise DataSourceError(f"V2 CLI 失败: {e}")

def get_today() -> dict:
    """调 V2 CLI `today` → 返 dict"""
    # 同 get_balance 模式

def get_history(days: int = 7, limit: int = 50) -> dict:
    """调 V2 CLI `history --days N --limit M` → 返 dict"""
    # 同上, 加参数
```

**关键设计**:
- **subprocess 调 CLI**, 不直接解析 SQLite (那是 kids-points V2 团队的事)
- **5s timeout** (V2 CLI 纯读, 正常 < 0.1s, 5s 足够)
- **失败抛 DataSourceError**, server 层 catch + 返 HTTP 503 + 上次缓存
- **不缓存** (server 内存有缓存, 包装层不重复)

---

## 9. 里程碑

| 阶段 | 时间 (估) | 内容 | 状态 |
|---|---|---|---|
| **M0** | 2026-06-12 | 项目启动 (5 显示技术对比, 选型, 4 文件, 决策) | ✅ |
| **M0.5** | 2026-06-12 | 范围收窄 (业务=积分) + 完整设计文档 (本文件) | 🔄 本轮 |
| **M1** | 2026-06-12 → 06-16 | **桌面 dashboard 端到端** (主战场, 仿真+部署+验证) | 📋 |
| M1.1 | 06-12 → 06-13 | 仿真先行 (pygame 4 区视觉, 改字号零成本, 横/竖 2 套 ORIENTATION_CONFIGS) | ✅ |
| M1.2 | 06-13 → 06-14 | Python server (Flask + flask-sock WS + watchdog V2 SQLite + V2 CLI 包装层) | ✅ (**v5.4 删 WS, 改 in-memory cache**) |
| M1.3 | 06-14 → 06-15 | ESP32 main.ino v1.1 (字号 + 中文 + 密码) + 本地编译验证 (Flash 1MB / RAM 52KB) | ✅ |
| M1.4 | 06-15 → 06-19 | 桌面端 USB 烧录 + 4 区 dashboard 渲染 + 双缓冲 + 5s 周期刷 + 店家伙 v2.0.7 库 | ✅ |
| M1.5 | 06-15 → 06-16 | 端到端验证: 改 balance.json → 板 <1s 更新 + systemd 落地 | 📋 |
| **M2** | ~~估 6/20+~~ | ~~挂墙屏 (4 块 P2 320×160 × 1×4)~~ — **06-15 老王拍板取消**: 改走 desktop 主线, 11 寸 (P2 128×96) 桌面 dashboard 走到底. 物理尺寸 28×20cm 跟桌面摆放 + 单人观看够用. M2 挂墙 (4 块拼 20+ 寸横幅) 留作"未来想放大再做" (不主动规划). | ~~📋~~ |
| **M3+** | 未来 | 夜间模式 / 字体 / 滚动 / OTA 文档化 | 📋 |

**下周二 6/16 deadline** = M1 全部完成. M2 挂墙不阻塞.

---

## 10. 风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| **¥190 板未到 6/16** | M1.4 烧录延期 | 仿真先行 (M1.1) + code 完整, 板到即烧 |
| V1 改 schema | dashboard 解析失败 | 单点 adapter, V1 字段变化一处改 |
| inotify 在容器/sandbox 不通 | 推失效 | 退化到 5min 轮询 (主路径仍工作) |
| Flask 端口冲突 | 起不来 | 先 `ss -tlnp \| grep 8080` 查, 不通改 8088/9000 |
| 老王忘关 V1 引用计数 | (无, 我们读 V1 不写) | - |
| 中文字体 8px 在 128px 宽挤 | 流水行超宽 | 截断到 12 字符 + M3 滚动 |
| 网络抖动 (Wi-Fi 抖) | WS 推失败 | 5min 轮询兜底, ESP32 重连 WS |
| kids-points 漏扣 (V1 5/19 之前 11 条) | 显示数字与 V1 历史对不上 | 不修复 (V1 永不动), 文档说明 |

---

## 11. 关键决策 (本轮新增)

### D9. 2026-06-12 — 业务范围收窄 = 积分展示
- 不做通用 todo / 计划单
- 看板 = kids-points V1 的只读视觉
- 录入在 V1 飞书 agent (永不动)

### D10. 2026-06-12 — 数据源 = V1 balance.json
- 不用 SQLite (V2 暂不接)
- 不用自建 JSON (与 V1 双写易脱节)
- 路径 configurable, 默认 V1

### D11. 2026-06-12 — 推送触发 = inotify 监听
- 不用 webhook (V1 永不动, 不能让 V1 调我们的 API)
- 不用 cron 频繁轮询 (浪费 CPU, 推延迟高)
- inotify 端到端 <1s, 完美

### D12. 2026-06-12 — 双保险频率 = 5min (主) + 即时 (推)
- 主 5min: 看板量级够用, 不烧 CPU
- 推即时: 体验好, 用户操作后秒刷
- 频率可调 (M3 加 env var / config)

### D16. 2026-06-12 下午 — Linux 服务器 IP = YOUR_SERVER_IP
- 老王路由器 DHCP 分配, 自查 `ip addr` 确认 (`wlp0s20f3` 无线网卡, 192.168.50.1 网关)
- ping 自测: 0.014ms, 本机 = server, 局域网内极快
- ESP32 config 块写死 `http://YOUR_SERVER_IP:8080`

### D17. 2026-06-12 下午 — Wi-Fi SSID = YOUR_WIFI_SSID, 密码 = YOUR_WIFI_PASSWORD
- 老王提供, ESP32 config 写死
- 2.4GHz 频段 (本机走无线网卡, ESP32 仅支持 2.4G, 兼容)
- ⚠️ 烧录前老王再 double check 一次密码 (我没机会实测 ESP32 连)

### D18. 2026-06-12 下午 — 看板标题 = Kid Dashboard
- 老王拍板, dashboard JSON `title` 字段固定
- 默认值改自原 "KID POINTS" (M0.5 临时默认)

### D19. 2026-06-12 下午 — 板到货日 = TBD (老王手动通知)
- 闲鱼快递, 板到即 M1.4 解锁
- 不阻塞 M1.1 (仿真) / M1.2 (Python) / M1.3 (ESP32 写代码)
- M1.1-M1.3 全部可今起开干, 板到即烧

### D20. 2026-06-14 — 数据源 = kids-points V2 SQLite (via CLI)
- **跟 V0.2 D10 反转**: 之前数据源 = V1 balance.json, 现在 = V2 SQLite
- V2 团队 (老王) 给 dashboard 留了 3 个 CLI 接口 (2026-06-14 MVP 落地), 本项目用包装层调
- V1 永不动硬约束**保持** (跟 V0.2 一样) — 本项目只读 V2, 不动 V1
- V2 production DB 数据稀疏是 design 行为 (V2 promotion 之前 DB 不增长), 不算 bug
- 详细: § 3 数据源, `kids-points` skill § "MVP 兼容性 (2026-06-14 dashboard CLI)"

### D21. 2026-06-14 — 双保险频率 = 30s (主) + 即时 (推, inotify V2 SQLite)
- **跟 V0.2 D12 反转**: 之前 5min 拉, 现在 30s 拉
- 监听文件: V1 balance.json → V2 SQLite (`kids_points.db`)
- 30s 拉是 ESP32 端 CPU 友好频率, 用户发飞书后平均 15s 看到板更新 (5min 太长)
- V2 promotion 前 DB 不增长, 30s 拉空轮询无害 (V2 CLI 纯读, 0 token)
- 频率可调 (M3 加 env var / config)
- 详细: § 6 同步机制

---

## 12. 老王必答 (M1 启动前, 详见 notes.md 🟡)

> 阻塞 M1 烧录/部署, 不阻塞 M1 写代码.
> ✅ **Q2.1 / Q3.1 / Q3.2 / Q7.x 已答 (2026-06-12 下午)**, 仅剩 Q4.1 板到货日.

- [x] ✅ **Q2.1**: Linux 服务器 IP = `YOUR_SERVER_IP` (自查 `ip addr` + `ping` 0.014ms 确认, 无线网卡 `wlp0s20f3`, 网关 192.168.50.1)
- [x] ✅ **Q3.1**: Wi-Fi SSID = `YOUR_WIFI_SSID`
- [x] ✅ **Q3.2**: Wi-Fi 密码 = `YOUR_WIFI_PASSWORD`
- [ ] ❓ **Q4.1**: ¥190 板预计到货日 (老王手动通知)
- [x] ✅ **Q7.x**: 看板标题 = `Kid Dashboard`
- [ ] ❓ **Q9.1**: V2 promotion 状态 — 老王拍板 promote 时间 (kids-points V2 promotion 之前, dashboard 板显示的 V2 余额跟 V1 实际余额对不上, 因为 V2 production DB 还没数据; V2 promotion 之后这个问题自动消失). 答完可决定: (a) M1 验收时是 V1 balance 还是 V2 production DB? (b) 板到货后 V2 promotion 还没拍, 先用 V1 兜底, 等 V2 promotion 切?

> 答完 Q4.1 → M1.4 烧录/部署可启动. M1.1-M1.3 (仿真/Python/ESP32 代码) 今起可开干, 不烧板.
> 答完 Q9.1 → M1.5 端到端验证预期明确. 不阻塞 M1 写代码.

---

## 13. 下一步行动

按 `kanban.md` M1 backlog 顺序, 老王额度空档时:
1. 仿真 pygame 4 区 (M1.1) — 0 烧录, 0 风险
2. 写 Python server (M1.2):
   2a. 写 `code/server/data_source.py` (V2 CLI 包装层, 调 `balance` / `today` / `history` 3 接口, 5s timeout, 失败抛 `DataSourceError`)
   2b. 写 `code/server/server.py` (Flask + WS + inotify V2 SQLite + systemd), 调 data_source 拿数据, 包装成 § 4 dashboard JSON
   2c. 本机起服务, `curl http://localhost:8080/api/dashboard` 验证返 JSON
3. 写 ESP32 main.ino (M1.3) — Arduino 仿真器先看渲染, 30s 拉 + WS 收
4. 烧录 + 联调 (M1.4-M1.5) — 需板到货 + 必答资源齐 + V2 promotion 状态明确 (Q9.1)
