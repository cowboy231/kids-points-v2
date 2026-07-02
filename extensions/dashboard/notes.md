# 项目笔记 (Notes & Decisions)

> 这里记录跟老王讨论的事项 + 决策. 看板状态见 `kanban.md`, 完整设计见 `docs/plan.md`.

---

## 🔴 老王必答 (M1 烧录/部署前)

> 阻塞 M1.4 烧录/部署, **不阻塞** M1.1 (仿真) / M1.2 (Python) / M1.3 (ESP32 写代码).
> ✅ **Q2.1 / Q3.1 / Q3.2 / Q7.x 已答 (2026-06-12 下午)**, ✅ **M1.1 / M1.2 / M1.3 完成 (2026-06-15)**, ❓ **Q4.1 板到货日** + **Q9.1 V2 promotion 状态 (2026-06-14 新增)**.
> 答完 Q4.1 即解锁 M1.4. 答完 Q9.1 明确 M1.5 验收源 (V1 vs V2 production DB).

### Q2. 家里 Linux 服务器 IP ✅ (2026-06-12 下午)

- **Q2.1**: ✅ `YOUR_SERVER_IP` (本机 `wlp0s20f3` 无线网卡, 网关 `192.168.50.1`, 自查 `ip addr` + `ping` 0.014ms 确认)

### Q3. 家里 Wi-Fi ✅ (2026-06-12 下午)

- **Q3.1**: ✅ SSID = `Asur737`
- **Q3.2**: ✅ 密码 = `q2lrLIvUs`
- **Q3.3**: ✅ 频段 2.4GHz (本机走无线网卡 wlp0s20f3, ESP32 仅支持 2.4G, 自然兼容)

### Q4. ¥190 板到货 ❓ (M1.4 仍待)
- **Q4.1**: 老王 "我到时候会手动告诉你" — 板到货日 TBD, 板到即通知
- 验货 checklist: M1 写 `docs/hardware.md` (老王 5 分钟, 测 USB-C 供电 + HUB75 显示测试图)
- **不阻塞**: M1.1 (仿真) / M1.2 (Python) / M1.3 (ESP32 写代码) 今起可开干

### Q9. V2 promotion 状态 (新增, 2026-06-14)
- **Q9.1**: kids-points V2 promotion 拍板时间 (老王决定)
  - V2 promotion 之前, dashboard 板显示的 V2 余额跟 V1 实际余额对不上 (V2 production DB 数据稀疏, design 行为)
  - V2 promotion 之后, V2 飞书 bot 直接写 V2 production DB, dashboard 实时同步
  - 答完可决定: (a) M1 验收时是 V1 balance 还是 V2 production DB? (b) 板到货后 V2 promotion 还没拍, 先用 V1 兜底, 等 V2 promotion 切?
- **不阻塞** M1 写代码 (data_source.py 调 V2 CLI, 调不通返 503 + 缓存, 不会因 V2 promotion 状态卡住)
- **阻塞** M1.5 端到端验收 (需要明确验收源是 V1 还是 V2 production DB)

### Q7.x. 看板标题 ✅ (2026-06-12 下午)

- **Q7.x**: ✅ `Kid Dashboard` (老王拍板, D18)

---

## 🟡 老王可答 (影响 M2+ 进度, 不急)

### Q5. 桌面 dashboard 外壳
- **Q5.1** 摆哪: 书房? 客厅? 卧室?
- **Q5.2** 外壳材料: 亚克力 (¥30) / 木框 (¥50-100) / 3D 打印 (¥100+) / 现成塑料相框 / 裸放 (¥0)
- **Q5.3** 视角: 桌面平放 / 桌面立放 (墙挂式)?

### Q6. 挂墙屏外壳 (M2+)
- **Q6.1** 挂哪: 客厅墙 / 走廊 / 儿童房门口?
- **Q6.2** 离地高度: 儿童平视 / 大人平视?
- **Q6.3** 外壳材料: 铝型材 (¥200-400) / 木框 (¥100-200) / 裸挂 (¥0)

### Q7. 业务功能 (M3+)
- **Q7.1** 倒计时: 距离睡觉 / 距离上学?
- **Q7.2** 天气: 接和风/高德 API?
- **Q7.3** 日历: 老王飞书日历事件?
- **Q7.4** 字体升级: 8×8 → 16×16 易读?
- **Q7.5** 二维码: 微信扫码看详情?
- **Q7.6** 多页轮播: 内容太多分页?
- **Q7.7** 长内容滚动: 流水 description 超 12 字符滚动?

### Q8. 数据同步细节 (M3+)
- **Q8.1** 5min 频率是否合适 (太密/太疏)?
- **Q8.2** 失败重试策略: 重试 3 次用本地缓存?
- **Q8.3** 推送触发: inotify (默认) / 加 cron 兜底?

---

## 🟢 决策记录 (已定, 存档)

### D1. 2026-06-12 — 显示技术选定 LED 矩阵
- 排除 LCD (蓝光), 排除投影 (白天差), 排除 e-ink (20" 贵)
- HUB75 单元板, 黑底 + 琥珀 (R=255, G=140, B=0) + 关蓝
- 1m+ 视距 = 反射光为主, 0 蓝光, 护眼 ≈ e-ink

### D2. 2026-06-12 — 控制板选定 ESP32
- 排除 Pi (¥350+, 启动 30s, 功耗 5W)
- 选定 ESP32-WROOM-32 + HUB75E 适配板 (¥30-80, 1s 启动, 0.5W)
- 内置 2.4GHz WiFi + BLE

### D3. 2026-06-12 — 桌面板子选定 ¥190 P2 128×96
- ¥190 = 12-25% 市场价, 卖家全好 + 已焊 ESP32 (待验)
- 物理 256×192mm = 11" 4:3, 桌面紧凑
- 1/32 扫高密度, P2.0mm 间距

### D4. 2026-06-12 — 挂墙板子选定 4 块 P2 320×160 × 1×4 (M2+)
- 4 块横拼 = 1280×160mm = 50" 8:1 横幅
- 适合"游戏简报"长内容
- 1 块带 ESP32 + 3 块不带, 省 ¥600

### D5. 2026-06-12 — 架构选定双保险 (HTTP 拉 + WS 推)
- 主: ESP32 5min 拉 `GET /api/dashboard`
- 备: inotify 监听 V1 balance.json → Flask → WS → ESP32 立即拉
- 不需要 MQTT (看板量级 over-engineering)

### D6. 2026-06-12 — 软件栈选定
- ESP32: mrcodetastic/ESP32-HUB75-MatrixPanel-DMA + ArduinoJson + ESPAsyncWebServer
- Python: Flask + websockets (server) + watchdog (inotify) + systemd

### D7. 2026-06-12 — 散热选定 静态
- IC 散热片 + 铝壳 (无风扇)
- 游戏简报暗模式, 60-70% 像素常关, 热量低
- 老王怕吵, 风扇否决

### D8. 2026-06-12 — 电源选定 1 块合 1
- 桌面 1 块 5V 3A
- 挂墙 1 块 5V 8A + 电源分配板 (M2+)
- 干净, 易维护

### D9. 2026-06-12 — 业务范围收窄 = 积分展示
- 不做通用 todo / 计划单 / 日报
- 看板 = kids-points V1 的只读视觉
- 录入在 V1 飞书 agent (永不动)

### D10. 2026-06-12 — 数据源 = V1 balance.json
- 不用 SQLite (V2 暂不接)
- 不用自建 JSON (与 V1 双写易脱节)
- 路径 configurable, 默认 `~/.openclaw/agents/kids-study/workspace/kids-points/balance.json`

### D11. 2026-06-12 — 推送触发 = inotify 监听
- 不用 webhook (V1 永不动, 不能让 V1 调我们的 API)
- 不用 cron 频繁轮询 (浪费 CPU, 推延迟高)
- inotify 端到端 <1s, 完美

### D12. 2026-06-12 — 双保险频率 = 5min (主) + 即时 (推)
- 主 5min: 看板量级够用, 不烧 CPU
- 推即时: 体验好, 用户操作后秒刷
- 频率可调 (M3 加 env var / config)

### D13. 2026-06-12 — 服务器 = 本机 Linux
- 老王确认 "Linux 服务器就是这台机器本身"
- 跑 Flask on 0.0.0.0:8080
- systemd 7×24 自启

### D14. 2026-06-12 — 网络 = 当前网络
- 老王确认 "密码和网络也就是你现在的网络"
- Wi-Fi SSID/密码: 老王必答 (Q3.1/Q3.2)
- ESP32 config 写死, 烧录后 0 接线更新靠 OTA

### D15. 2026-06-12 — Deadline = 下周二 6/16
- M1 (桌面 dashboard 端到端) 必达
- M2 (挂墙屏) 不阻塞
- 仿真先行, 板不到也能跑通链路

### D16. 2026-06-12 下午 — Linux 服务器 IP = YOUR_SERVER_IP
- 老王路由器 DHCP 分配, 自查 `ip addr` 确认 (`wlp0s20f3` 无线网卡, 网关 192.168.50.1)
- ping 自测: 0.014ms, 本机 = server, 局域网内极快
- ESP32 config 块写死 `http://YOUR_SERVER_IP:8080`

### D17. 2026-06-12 下午 — Wi-Fi SSID = Asur737, 密码 = q2lrLIvUs
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

### D20. 2026-06-14 — 数据源 = kids-points V2 SQLite (via CLI 包装)
- **跟 D10 反转**: 之前 V1 balance.json → 现在 V2 SQLite
- kids-points V2 团队 (老王) 给 dashboard 留了 3 个 CLI 接口 (2026-06-14 MVP), 详细看 `kids-points-runtime/HANDOVER.md` § 4.4 + `kids-points` skill § "Dashboard CLI 模式"
- V1 永不动硬约束**保持** (跟 D10 一样) — 本项目只读 V2, 不动 V1
- V2 production DB 数据稀疏是 design 行为 (V2 promotion 之前 DB 不增长), 不算 bug
- 新增 `code/server/data_source.py` (V2 CLI 包装层, 调 `balance` / `today` / `history` 3 接口, 5s timeout)
- 3 个 CLI 接口实测 OK (2026-06-14):
  - `cli.py balance` → `{balance, balance_display, as_of, source: "v2_sqlite"}`
  - `cli.py today` → `{date, income, expense, net, tx_count, balance, balance_display}`
  - `cli.py history --days 7 --limit 5` → `{from, to, days, tx_count, history: [{date, time, type, amount, description}]}`
- 详细: `docs/plan.md` § 3 数据源 v0.3

### D21. 2026-06-14 — 双保险频率 = 30s (主) + 即时 (推, inotify V2 SQLite)
- **跟 V0.2 D12 反转**: 之前 5min 拉, 现在 30s 拉
- 监听文件: V1 balance.json → V2 SQLite (`kids_points.db`)
- 30s 拉是 ESP32 端 CPU 友好频率, 用户发飞书后平均 15s 看到板更新 (5min 太长)
- V2 promotion 前 DB 不增长, 30s 拉空轮询无害 (V2 CLI 纯读, 0 token)
- 频率可调 (M3 加 env var / config)
- 详细: `docs/plan.md` § 6 同步机制 v0.3

### D22. 2026-06-15 — ESP32 库选型 (M1.3 v1)
- **HUB75 驱动**: mrcodetastic/ESP32-HUB75-MatrixPanel-DMA (DMA 模式, 1/32 扫支持, 关蓝靠不写 B 通道实现, GitHub 6K+ stars)
- **JSON 解析**: ArduinoJson 6.x (跟 server.py schema 1:1, 1024 byte 静态 doc 够 dashboard JSON 用)
- **WebSocket + HTTP**: ESP32Async/ESPAsyncWebServer + AsyncTCP (80 端口, 收 refresh + 4 调试接口)
- **OTA**: ArduinoOTA 内置 (Wi-Fi 推更新, 主机名 `dashboard-esp32`)
- **字体**: Adafruit GFX 5x7 内置 (v1 仅 ASCII 数字英文; v1.1 加 u8g2 12x12 中文)
- 排除: rpi-rgb-led-matrix (要 Pi, 不是 ESP32 库) / LedControl (MAX7219, 跟 HUB75 不兼容) / FastLED (单线 WS2812, 跟 HUB75 不兼容)
- 详细: `code/esp32/desktop/README.md` 库依赖表

### D23. 2026-06-15 — WS 路径确认: ESP32 端起 WS server (vs 推 Push 给 ESP32 端)
- **原方案** (v0.2 06-12): ESP32 起 WS server, server 推 refresh → ESP32 收
- **v0.3 反转可能**: Flask server 推 WebSocket 给 ESP32
- **D23 拍板**: 维持 v0.2 原方案 — ESP32 端起 WS server, Flask 用 push 端点触发 inotify → flask-sock 推给 ESP32
- 理由: ESP32 在内网, 起 server 比 client 简单 (不需要 ESP32 主动去连 Flask); Flask 在 server 端管所有 WS client 状态, 推逻辑跟现有 watchdog 整合
- 详细: `docs/plan.md` § 6 同步机制 v0.3 + `code/server/server.py` WS 实现

### D24. 2026-06-15 — M1.3 v1.1 编译路上踩的坑 (沉到 `home-dashboard-display` skill)
- 1) **ESP32 平台 3.x 跟 ESPAsyncWebServer 3.1.0 双重不兼容** (mbedtls API `md5_finish_ret` + `pxCurrentTCB` undefined). 走 **2.0.17** 才稳.
- 2) **HUB75 v3 库头文件改名** `ESP32-HUB75-MatrixPanel-DMA.h` → `ESP32-HUB75-MatrixPanel-I2S-DMA.h`.
- 3) **HUB75_I2S_CFG 构造器第 4 参数是 `i2s_pins` struct** 不是 int. 用 `HUB75_I2S_CFG(W, H, chain)` 3 参数走默认 pin.
- 4) **arduino-cli 编译期待主文件跟目录同名** (`desktop.ino` not `desktop-dashboard.ino`). 改文件名 + 改 README 引用.
- 5) **esptool 4.5+ 需要 pyserial** (`pip install pyserial` 装到 hermes venv).
- 6) **U8g2 + U8g2_for_Adafruit_GFX 桥接**: 库叫 `U8g2_for_Adafruit_GFX` (olikraus), 用法 `U8G2_FOR_ADAFRUIT_GFX u8g2; u8g2.begin(*dma_display); u8g2.setFont(u8g2_font_unifont_t_chinese1);` 渲染中文.
- 7) **arduino-cli lib install 库名**: 空格分隔不连字符. 例: `ESP32 HUB75 LED MATRIX PANEL DMA Display` (库名).
- 8) **ESP32 平台 2.0.17 跟 mbedtls 2.x**: `mbedtls_md5_*_ret` 跟 `mbedtls_md5_*` deprecated 都还在, 用 `_ret` 跟 ESP32 2.0.17 + 3.x 都兼容.
- 9) **降版本自动卸老版本**: `arduino-cli core install esp32:esp32@2.0.17` 自动卸 3.3.10 libs.
- 详细: `docs/plan.md` v0.6 changelog + `~/.hermes/memory.md` 2026-06-15 ESP32 arduino-cli 编译段.

### D25. 2026-06-15 — Scope 变更: 取消 M2 挂墙路线, 整版 11 寸走 desktop dashboard 主线
- **触发**: 老王重新看了 ¥190 板子淘宝说明, 发现物理尺寸 28×20cm ≈ 11 寸, 跟最初"至少 20 寸"期望有差距. 但同时说"已经改成做 dashboard 而不是挂墙了, 所以 OK 的"
- **决策**: 11 寸 (P2 128×96) 桌面 dashboard 走到底, **M2 挂墙 (4 块拼 20+ 寸横幅) 取消**, 留作"未来想放大再做", 不主动规划
- **理由**: 11 寸 + 桌面摆放 + 单人观看 + 桌面 dashboard 路线够用. 挂墙横幅 4 块拼接成本高 (¥190 × 4 + 5V/20A 电源 + 边框), 跟当前 use case (孩子完成积分后抬头看一眼) 不匹配
- **新机会 (TF 卡槽)**: 板自带 TF 卡槽, v2 候选可做离线 fallback + 静态/动态 GIF 缓存. 估 +1-2h, 不阻塞 M1.4
- **影响**:
  - plan.md M2 任务改 "取消 (06-15 scope 变更)"
  - M1.4 仍是等 Q4.1 板到货, 1h 烧录
  - 端到端 (M1.5) 估 4h, 总 1 周 (6/12 → 6/19) 仍可
  - README.md 项目结构 v0.7 同步: `code/esp32/wall/` 路径标注 "M2 取消, 留作未来"
  - 不动 M1 任何代码 (11 寸 P2 128×96 跟我代码一致)

---

## 🆕 2026-06-14 — 数据源迁移 (D20/D21) 沉淀

### 触发

老王在 kids-points V2 promotion 拍板路径上, 顺手给 kids-points V2 加了 CLI 命令行功能 (3 接口: `balance` / `today` / `history`), 跟 dashboard 项目对接。老大原话: "我更新了数据的来源, 那我给我的积分Scale增加了CLI命令行的功能, 然后里边有这三个接口。你可以阅读这份文档, 找到它的CLI接口和它的数据格式。我希望你把这部分内容也更新到你的这个项目文档里。"

### 关键洞察 (避免下次踩坑)

1. **"数据源 = 切" 跟"硬约束 = 不动 V1" 不冲突**:
   - 老王说"我更新了数据来源"= 数据源从 V1 切到 V2
   - kids-points 硬约束"V1 永不动"= 本项目不写 V1
   - "读 V2" 跟 "不动 V1" 完全兼容 — 读 ≠ 写
   - 跟 kids-points 06-14 09:30 拍板的 "MVP dashboard CLI 兼容方案" 对齐

2. **"V2 production DB 数据稀疏" 不是 bug**:
   - V2 promotion 之前, V2 走 replay.py 批处理, 写在隔离 DB
   - production DB 没新数据, dashboard 看到 0 笔 / 余额停在老数据是**正常**
   - 跟 V2 promotion 状态强相关, 不是 dashboard 项目的问题
   - V2 promotion 之后这个问题自动消失 (V2 飞书 bot 直接写 production DB)

3. **3 个 CLI 接口覆盖 dashboard 全部需求**:
   - `balance` → `total_balance` + `last_updated`
   - `today` → `today_count` + `today_net`
   - `history --days 1 --limit 3` → `recent` (3 行)
   - dashboard 4 区 (标题/3 行流水/今日动帐/总积分) 全部由 V2 CLI 提供

### 决策转变的"废"标记

D10 / D11 / D12 不删除, 加 "废弃" 标记和"反转"指向, 保留历史可追溯:
- D10 → D20 (V1 → V2)
- D11 → D21 (V1 文件 → V2 SQLite)
- D12 → D21 (5min → 30s)

---

## 📞 老王联系方式

- 飞书群: Hermes
- Thread: omt_194f96638accdbef
- 老王时区: GMT+8

---

## 📁 关键文件路径

| 用途 | 路径 |
|---|---|
| 项目根目录 | `/home/wang/projects/kids-points-v2/extensions/dashboard/` |
| 看板 | `/home/wang/projects/kids-points-v2/extensions/dashboard/kanban.md` |
| 完整设计 | `/home/wang/projects/kids-points-v2/extensions/dashboard/docs/plan.md` |
| 项目说明 | `/home/wang/projects/kids-points-v2/extensions/dashboard/README.md` |
| 桌面 ESP32 代码 (M1 实施) | `/home/wang/projects/kids-points-v2/extensions/dashboard/code/esp32/desktop/desktop-dashboard.ino` |
| 挂墙 ESP32 代码 (M2+) | `/home/wang/projects/kids-points-v2/extensions/dashboard/code/esp32/wall/wall-display.ino` |
| Python Flask server (M1 实施) | `/home/wang/projects/kids-points-v2/extensions/dashboard/code/server/server.py` |
| 仪表板 JSON schema | `/home/wang/projects/kids-points-v2/extensions/dashboard/code/data/balance_view.json` |
| V1 源数据 (永不动, V0.3 后本项目不再读) | `~/.openclaw/agents/kids-study/workspace/kids-points/balance.json` |
| **V2 CLI 入口 (新加, 2026-06-14)** | `/home/wang/projects/kids-points-v2/runtime/cli.py` |
| **V2 production DB (新加, 2026-06-14, dashboard 只读)** | `/home/wang/projects/kids-points-v2/runtime/data/kids_points.db` |
| **V2 CLI 包装层 (新加, M1.2 实施)** | `/home/wang/projects/kids-points-v2/extensions/dashboard/code/server/data_source.py` |
