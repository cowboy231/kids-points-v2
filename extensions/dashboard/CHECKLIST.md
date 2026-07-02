# 启动 Checklist (M0.5 → M1)

> 看板 M0.5 完成 = 这个 checklist M0/M0.5 全部 ✅
> 推进 M1.1 (仿真) 之前必读
> 完整设计: `docs/plan.md` | 看板: `kanban.md` | 决策: `notes.md`

---

## M0: 项目启动 (✅ 2026-06-12)

### 文件夹
- [x] `/home/wang/projects/kids-points-v2/extensions/dashboard/` 项目根目录建好
- [x] `code/esp32/desktop/` 桌面端代码 (骨架)
- [x] `code/esp32/wall/` 挂墙端代码 (骨架)
- [x] `code/server/` Python server
- [x] `code/data/` 数据文件
- [x] `docs/` 文档

### 文档
- [x] `README.md` 项目说明
- [x] `kanban.md` 项目看板
- [x] `notes.md` 讨论 + 决策记录
- [x] `CHECKLIST.md` 启动 checklist (本文件)

---

## M0.5: 范围确认 + 完整设计 (🔄 2026-06-12)

### 范围收窄
- [x] 业务 = 只展示积分 (V1 kids-points)
- [x] 4 区布局: 标题 / 3 行流水 / 本日动帐 / 总积分
- [x] 5min 拉 (主) + inotify 触发推 (备)
- [x] 数据源 = V1 `balance.json` (只读, 永不动 V1)

### 完整设计
- [x] `docs/plan.md` 完整设计文档 (v0.2, 13 节)
- [x] `notes.md` 决策记录更新 (D1-D15)
- [x] `kanban.md` 任务拆解 (M0.5-M3+)
- [x] `README.md` 项目说明同步

### 老王必答 (M1.4 烧录前, 详见 `notes.md` 🔴)
- [x] ✅ **Q2.1**: 家里 Linux 服务器 IP = `YOUR_SERVER_IP` (自查确认)
- [x] ✅ **Q3.1 / Q3.2**: Wi-Fi SSID = `YOUR_WIFI_SSID` / 密码 = `YOUR_WIFI_PASSWORD` (2.4GHz 兼容)
- [ ] **Q4.1**: ¥190 板预计到货日 (老王手动通知)
- [x] ✅ **Q7.x**: 看板标题 = `Kid Dashboard`

---

## M1: 桌面 dashboard 端到端 (🔄 06-12 → 06-16, M1.1/M1.2 ✅)

### M1.1 仿真先行 (0 烧录, 0 风险) — 06-12 → 06-13 ✅
- [x] 写 `code/sim/desktop_sim.py` (pygame 128×96 横版模拟, 4 区布局)
- [x] 仿真数据用 V2 CLI 实时拉 (production DB 数据稀疏 → 显示"等待" 占位)
- [x] 跑仿真, 老王拍板字号/颜色/布局 (v1 横版 OK)
- [x] v1.3 横/竖 2 套 ORIENTATION_CONFIGS 持久化 (vertical 96×128 4 区 y 32/56/80/108/112 + 字号 36/24/24)
- [x] `tune.py --orientation {horizontal,vertical}` 切换, 2 张 PNG 仿真 OK (`/tmp/sim_tune_{horizontal,vertical}_sparse.png`)
- [x] `set_orientation()` 函数 (代码内切横竖)

### M1.2 Python server — 06-13 → 06-14 ✅
- [x] `code/server/data_source.py` (V2 CLI 包装层, 调 balance/today/history, 5s timeout, DataSourceError)
- [x] `code/server/server.py` (Flask + flask-sock WS + watchdog V2 SQLite inotify)
- [x] GET `/api/dashboard` (返 § 4 dashboard JSON)
- [x] GET `/health` (返 `{"ok": true}`)
- [x] WS `/ws` 推 `{"type": "refresh"}` (watchdog 触发 + 启动时初始 1 次)
- [x] 失败兜底: `/tmp/dashboard_cache.json` (上次成功) → 全占位 `{"_error": ...}`
- [x] 启动时拉 1 次缓存
- [x] `code/server/dashboard.service` (systemd 单元, M1.5 落 `/etc/systemd/system/`, 本轮无 sudo 仅写 + 手动跑验证)
- [x] 端口检查 (`ss -tlnp | grep 8080`)
- [x] 本地验证 (`curl http://localhost:8080/api/dashboard` + WS 推 + inotify 触发推)

### M1.3 ESP32 main.ino — 06-14 → 06-15 ✅ (编译验证待 M1.4 烧录)
- [x] 改 `code/esp32/desktop/desktop-dashboard.ino` 4 区布局 (横 128×96, 物理 y 跟 sim 1:1)
- [x] HTTP 拉 (30s 一次, 跟 M1.2 server `/api/dashboard` 对接)
- [x] WS 收 (服务器推 refresh 立即拉, ESP32 端 `/ws` AsyncWebSocket)
- [x] 本地缓存 (RAM `last_good` struct, 网络挂显示上次)
- [x] 关蓝通道 (B=0, 配色 `COLOR_AMBER = 0xFF8C00` R=255 G=140 B=0)
- [x] OTA 升级 (ArduinoOTA, 主机名 `dashboard-esp32`)
- [x] Arduino IDE 编译验证 (库: mrcodetastic/ESP32-HUB75-MatrixPanel-I2S-DMA + ArduinoJson 7.x + ESPAsyncWebServer 3.1.0 + AsyncTCP + U8g2 + U8g2_for_Adafruit_GFX) — ✅ **arduino-cli 1.5.1 + ESP32 2.0.17 编译通过** (Flash 1MB 78% / RAM 52KB 15%, 0 错误 0 警告)
- [x] `code/esp32/desktop/README.md` 库依赖 + 编译配置 + 烧录步骤 + 4 调试接口
- [x] 调试接口: `/health` / `/refresh` (立即拉) / `/setup?brightness=N` (调亮度) / `/ws` (推 refresh)

### M1.4 桌面端首次烧录 — 06-15 (板到货后)
- [ ] 5 分钟验货 (待写 `docs/hardware.md`)
- [ ] USB 烧录
- [ ] Wi-Fi 配网
- [ ] 服务器 IP 配
- [ ] 板显示静态 (验证 HTTP 拉取)
- [ ] WS 推验证 (板端 WS 连上, 服务器侧触发推, 板 <1s 更新)

### M1.5 端到端验证 — 06-15 → 06-16
- [ ] 改 V1 balance.json → 板 <1s 更新
- [ ] 5min 兜底 (关 inotify, 等 5min, 板也能拉)
- [ ] 网络断 (拔服务器网线, 板显示 last good, 不白屏)
- [ ] 恢复 (插回网线, 板 <5min 内恢复)
- [ ] 24h 稳定性 (systemd 日志无 OOM / 内存泄漏)

---

## M2: 挂墙屏 (📋 估 6/20+, 不阻塞 M1)

- [ ] 采购 4 块 P2 320×160 (1 块带 ESP32)
- [ ] 采购 5V 8A 电源 + 分配板
- [ ] 采购 HUB75 16P 排线 × 5
- [ ] 采购外壳材料 (待 Q6 答)
- [ ] ESP32 端 4 屏级联 main.ino
- [ ] HUB75 菊花链接线
- [ ] 首次烧录 + 配网
- [ ] 拉取验证
- [ ] 亮度均匀性
- [ ] 挂墙外壳组装

---

## M3+: 优化 (📋 估 7 月起)

- [ ] 夜间模式 (0:00-6:00 降到 20% 亮度)
- [ ] 字体升级 (8px → 12px/16px)
- [ ] 长内容滚动
- [ ] OTA 流程文档化
- [ ] (可选) Web 录入页
- [ ] (可选) 天气/日历
- [ ] (可选) 倒计时
