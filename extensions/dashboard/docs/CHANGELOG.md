# CHANGELOG — Kids Dashboard 完整版本史

## v5.4 (2026-06-20) — Service 删 WS + in-memory cache

**老王决策**:
- WebSocket 已废弃 (ESP32 WebSocketClient 库 +50KB Flash 风险, B 方案 5s 拉 + memcmp 足够)
- Service 删 WS endpoint, 改用 watchdog 监听 V2 DB + in-memory cache (可靠性优先)
- cache 模式: 99% 请求走 cache (V2 没写就 0 subprocess), V2 挂掉时屏显示最后正常数据

**改动**:
- **删** `server.py`: `flask_sock` import + `Sock(app)` + `/ws` endpoint (~80 行) + `broadcast_refresh()` 函数
- **删** `requirements.txt`: `flask-sock>=0.7`, `websocket-client>=1.8`
- **加** `server.py`: `cache_lock` / `cache_data` / `cache_dirty` / `cache_last_fetch` / `cache_fetching` / `watchdog_observer` 模块变量
- **加** `mark_cache_dirty(reason)`: 标 cache 脏 (watchdog + /api/push 都用)
- **加** `get_cached_data()`: 双重检查锁, dirty 才 fetch, 命中直接返 cache
- **改** `V2DBHandler._maybe_emit()`: `broadcast_refresh()` → `mark_cache_dirty()`
- **改** `start_watchdog()`: 存 `watchdog_observer` 全局, `/health` 报 `is_alive()`
- **改** `GET /api/dashboard`: `fetch_data()` → `get_cached_data()` (99% 命中)
- **改** `GET /health`: 加 `cache.{dirty, age_sec, watchdog_alive}` 字段
- **改** `POST /api/push`: `broadcast_refresh()` → `mark_cache_dirty("manual")`
- **改** `main()`: 启动时预热 cache (`cache_data` + `cache_dirty=False`), 避免首次 GET 走 subprocess
- **改** port check: 加 `SO_REUSEADDR` (避 TIME_WAIT 误判)
- **删** docs: `plan.md` / `roadmap.md` / `INDEX.md` / `architecture.md` 4 处 WS 描述

**新数据流 (cache 模式)**:
```
V2 写 SQLite
    ↓
watchdog Observer (inotify) 检测 mtime 变化
    ↓
mark_cache_dirty("watchdog: ...") (微秒级, 不调 subprocess)
    ↓
ESP32 5s 拉 GET /api/dashboard
    ↓
Server: cache dirty?
    ├─ 否 → 返回 cache_data (0 subprocess, 1ms)
    └─ 是 → fetch_data() → 3 个 cli.py subprocess → 更新 cache → 返回
                  ↓ (失败)
                兜底: /tmp/dashboard_cache.json
```

**可靠性收益**:
- subprocess 调用: 720/小时 → 每天几次 (V2 写时)
- V2 / cli.py 挂掉: 屏显示最后正常数据 (cache 命中, 零影响)
- watchdog 死: `/health` 报 `watchdog_alive: false`, `POST /api/push` 手动恢复
- 端口 TIME_WAIT: 加 SO_REUSEADDR 解决 (原代码 bug)

**老王决策归档**:
- "可靠性优先" 是 v5.4 设计原则: 99% 路径走 cache, 失败隔离
- 删 WS 是 YAGNI (当前 5s 拉够用, 真要 <1s 推再加, 增量小)
- watchdog 改 cache invalidation 是 "化废为宝": 已有机制换用途, 不增复杂度

---

## v5.3 (2026-06-20) — 亮度 50 + 底栏位稳定

**老王决策**:
- 亮度 70 → 50 (50 比 70 看着更柔和)
- 底栏加 2 数字位空格 (今日跟总分挤, 数字位常变来变去)

**改动**:
- `BRIGHTNESS = 50` (50/255 ≈ 20% 满亮度, 比 70 (27%) 再降一档)
- 底栏 label: `"今日"` → `"今"` + `"总分"` → `"总"` (各省 12 px, 抵消新间隙)
- `today_buf` 格式 `"%+d"` → `"%+3d"` (固定 3 字符宽, 数字位稳定不再跳)
- `total_buf` 格式 `"%d"` → `"%3d"` (固定 3 字符宽, 跟 today 对称)
- `x` offset 间隙: `+ 2` → `+ 2 + 2*7` (加 14 px = 2 数字位, 视觉分离 14 px)

**最坏总宽验算** (today=+99, balance=100):
- "今"(12) + 1 + "+99"(21) + 16(2+14) + "总"(12) + 1 + "100"(19) = **82 px** ≤ 92 px (10 px 余量) ✅

**屏效果** (按 EN 后看):
```
今  +5          总  77         ← +5 绿, 总 77 琥珀, 中间 14 px 间隙
```
- 数字位不再跳 (固定 3 字符宽)
- 视觉上 "今" 和 "总" 不再挤, 数字位置稳定

**风险**:
- 标签短了 1 字 ("今日"→"今" / "总分"→"总"), 上下文还在, 不影响认读
- 蓝光红线: 0 改动, 红线机制继续生效

**老王决策归档**: v5.3 = 底栏位稳定 + 亮度再降. 标签缩 1 字是 "为视觉稳定性让位" 的取舍, 老王拍板.

---

## v5.2 (2026-06-19) — 亮度 70 + 蓝光护眼硬红线

**老王决策**:
- 亮度 100 → 70 (更柔和室内)
- 永久禁蓝光 (LED 蓝光 ~470nm 直接伤眼)

**改动**:
- `BRIGHTNESS = 70`
- 加 `BLUE_BIT_MASK = 0x001F` / `HAS_BLUE(color)` 宏
- 加 `#if HAS_BLUE(...)` 编译期硬检查, 调色板常量含 B>0 → `#error` 编译失败
- 所有调色板常量加 `B=0 ✅` 注释
- docs: esp32-code.md 加"蓝光护眼硬红线"章节, verify.md 加 Q16 FAQ

**红线验证**: 临时改 `COLOR_AMBER 0xFC40 → 0xFC41` (B=1) → 编译立即报错, 改回通过 ✅

**屏效果**: 亮度更柔和 + 颜色零蓝光 (琥珀/红/绿/黑), 跟 v4 琥珀一样护眼

**老王决策归档**: v5.2 是永久红线, 未来任何人加新颜色, 编译会失败. 这是**老王 2026-06-19 决策**, 跟"够用就好"风格一致.

---

## v5.1 (2026-06-19) — RGB 全彩启用 + 真 RGB565 颜色

**老王决策**: 启用全彩屏 (硬件是 RGB 全彩 HUB75, 之前误判单色)
**改动**:
- 颜色常量从 RGB888 改真 RGB565 (`0xFF8C00` → `0xFC40` 等)
- sign_color: + 绿 / - 红 / 0 琥珀
- 底栏今日净增: + 绿 / - 红 / 0 琥珀
- docs: esp32-code.md 加 Q6.5 颜色 FAQ

**修长期 bug**: v4.0-v5.0 颜色定义错, 实际显示偏暗绿黄, 不是真琥珀

**注**: 板子硬件是 RGB 全彩 (老王确认实际接线 G/B pin 都接了), 我之前误判为单色

---

## v5.0 (2026-06-19) — 亮度 100 + 底栏汉字 + 颜色区分

**老王决策**: 亮度 255 → 100 (室内日用)
**改动**:
- `BRIGHTNESS = 100`
- 底栏 `T+10 ALL:77` → `今日 +0 总分 77` (汉字, 4 段拆渲染)
- 颜色用"亮度代替"区分 +/- (后被 v5.1 全彩替代)

---

## v4.9 (2026-06-19) — 5 行流水

**老王要求**: 屏能显示 5 条流水 (当天只有 3 条, 需跨天补)
**改动**:
- `recent[3]` → `recent[5]`
- 渲染循环 `i < 3` → `i < 5`
- 加 `ROW_4_Y=78` / `ROW_5_Y=94`
- fetch 循环 `i < 3` → `i < 5`
- 行间距 16 px (Chinese 13 + 3 留白)
- `data_source.py` `--days 1 --limit 3` → `--days 7 --limit 5` (跨天补数据)

**验证**: server 启动 log 返 5 条 (06-19 × 3 + 06-17 × 2) ✅

---

## v4.8 (2026-06-19) — 智能渲染 (B 方案)

**老王担心**: 30s 拉一次 + 5s render 一次 → 数据没变也重画 → 屏闪
**老王选**: B 方案 (5s 拉 + memcmp 智能渲染)
**改动**:
- `FETCH_INTERVAL_MS = 30000` → `5000`
- `render_frame()` 头部加 `static DashboardData last_rendered` + `memcmp`
- 数据没变 → return (静默不重画)
- 数据变 → 重画一次

**资源**: Flash +0 KB, RAM +50 bytes, CPU < 2%

**验证**: 老王拍照确认"数据没变不闪" ✅

---

## v4.7 (2026-06-19) — GB2312 一级字库

**老王反馈**: "看动片" 显示 (实际 "看动画片" 缺 "画" 字)
**根因**: chinese3 574 字覆盖不全
**改动**:
- 字体 `u8g2_font_wqy12_t_chinese3` → `u8g2_font_wqy12_t_gb2312b` (5653 字)
- Flash +107 KB (1049 / 1310 = 80%)
- 删 v4.6 DEBUG 模式, 恢复正常 description 处理

**验证**: 老王拍照确认 "口算题 / 跳绳 / 看动画片 / 火花小数学 / 数学口算" 全显示 ✅

---

## v4.6 (2026-06-19) — DEBUG 模式 (临时)

**目的**: 排查 chinese3 是否真缺字
**改动**: 加 `#define DEBUG_MODE`, 强制覆盖 description 为 `看动画片 / 跳绳 / 口算题 / 算术 / 数学题`
**结果**: 验证字库缺 "画" / "题" → 直接升 gb2312b (v4.7)

---

## v4.5 (2026-06-18) — description 按 "|" 拆分

**老王反馈**: description "口算题 | 今天做了20道题" 太长, 溢出 96 屏
**改动**:
- ESP32 渲染时按 "|" ASCII 分隔符切 description
- 只取前半段 ("口算题" / "跳绳" / "看动画片")
- 无 "|" → fallback 切 6 中文字 (skip ASCII)

**server 端**: 不动 (中间层不应知道屏宽, 留给 client 决定)

---

## v4.4 (2026-06-18) — 微调布局 Y

**改动**: `DIVIDER_2_Y = 105` → `110`, `FOOTER_Y = 125` (留更多间距)

---

## v4.3 (2026-06-18) — 底栏长格式

**改动**:
- 底栏 `T77` → `T+10 ALL:77` (完整可读)
- `DIVIDER_2_Y = 100`, `FOOTER_Y = 122`
- 删 v4.2 DEBUG 模式

**格式**: `T+10 ALL:77` = 11 字符 × 7 px = 77 px, 装得下 96 屏

---

## v4.2 (2026-06-18) — 数字字体升 7×13

**老王反馈**: 数字 5×7 跟中文 12×13 baseline 不齐
**改动**:
- 数字字体 `u8g2_font_5x7_tr` → `u8g2_font_7x13_tr`
- 字符高 13 跟 chinese3 字符高 13 一致 → baseline 自动对齐
- DEBUG 模式覆盖 description 测试中文显示

---

## v4.1 (2026-06-18) — UTF-8 截断优化

**改动**:
- UTF-8 截断跳过 ASCII 字符 (数字/英文)
- 行 Y 坐标 30/48/66 (3 行均匀分布)
- `DIVIDER_1_Y = 15`

---

## v4.0 (2026-06-18) — 全 U8g2 接管

**老王反馈**: 数字中文 baseline 不齐, 多种字体混排混乱
**改动**:
- 全 U8g2 接管 (不再用 GFX 5×7)
- 切字体 `u8g2_font_wqy12_t_chinese3` (中文 12×13)
- 数字 `u8g2_font_7x13_tr` (ASCII 7×13, 高匹配 chinese 13)
- 去日期 (屏宽不够)
- 加 `mxconfig.gpio.e = 16` 强制 E pin
- baseline 对齐: 数字底部 = 中文底部

---

## v3.x (2026-06-17) — 字库 + 布局

- v3.1: 改 `ROW_TEXT_Y` / `DIVIDER_Y` 防压字
- v3.0: `ROW_TEXT_SIZE = 2 → 1` (字号缩到 5×7)

---

## v2.x (2026-06-12 ~ 06-17) — 物理拼 + 库适配

- v2.8: BRIGHTNESS 拉到 255 (室内拍照调试)
- v2.7: 关 AsyncWebServer/ArduinoOTA (-36 KB Flash + -2 KB RAM, I2S DMA 才能跑)
- v2.0: 店家伙 v2.0.7 + 100% 复刻 HUB75E.txt 配置 (PANEL_RES_X=96 PANEL_RES_Y=64 PANEL_CHAIN=2, SERPENT=false TOPDOWN=false)

---

## v1.x (2026-06-03 ~ 06-12) — 首次跑通

- v1.1: 加 U8g2_for_Adafruit_GFX 中文桥接
- v1.0: 基础 HUB75 + WiFi + HTTP GET + 显示 "BOOT" 文字

---

## 总学习曲线

| 阶段 | 时间 | 烧录次数 | 主要学习 |
|------|------|----------|----------|
| 硬件探索 | 6/3-6/5 | - | 选型 (LED vs LCD vs e-ink, 屏幕尺寸) |
| 初次烧录 | 6/5-6/12 | 24+ | 库版本错配 + fill_test |
| M1.4 调试 | 6/12-6/19 | 30+ | NVS / I2S / pinmap |
| v4.x 字体/布局 | 6/18-6/19 | 6 | chinese3 → gb2312b, baseline 对齐 |
| v4.8-v4.9 优化 | 6/19 | 2 | 智能渲染 + 5 行流水 |

总耗时 ~16 天, 总烧录 ~60+ 次, 终版 v4.9 ✅

---

## 老王贡献的决策 (按时间)

| 决策 | 时间 | 影响 |
|------|------|------|
| 选 LED 矩阵 (不用 LCD/e-ink) | 6/3 | 锁定 HUB75 |
| 96×128 (不用 192×64 等) | 6/12 | 物理拼 2 块 |
| 桌面板 (不用墙挂) | 6/14 | 散热要求低 |
| 像素风 (不用 Awtrix) | 6/14 | 自写不选现成 |
| 静态散热 (不用风扇) | 6/14 | 成本/噪音 |
| 1 电源 (不用 5V/12V 双路) | 6/14 | 简化布线 |
| 价格敏感 (≤300 RMB) | 6/14 | 选 ESP32 + HUB75 (≤150 RMB) |
| B 方案 (memcmp 智能渲染) | 6/19 | 5s 拉 + 不重画 |
| 5 行流水 (老王后续要求) | 6/19 | 改 recent[5] + 紧凑布局 |

---

## 关键数字回顾

- **库版本**: v2.0.7 店家伙 (不是 v3.0.14 自装)
- **字库**: gb2312b 5653 字 (Flash 107 KB)
- **Flash**: 1049 KB / 1310 KB (80%)
- **RAM**: 47 KB / 320 KB (14%)
- **FPS**: 0.2 (5s/render, memcmp 智能跳过)
- **CPU**: < 2%
- **WiFi 占用**: < 1% (设计寿命 MTBF > 50万小时)
- **Fetch**: 5s/次, server SQLite < 100 ms 响应
- **屏**: 96×128 LED 矩阵, 琥珀色, 桌面书桌摆
- **总成本**: ~150 RMB (ESP32 30 + HUB75 96×64 × 2 = 100 + 线材 + 电源 20)