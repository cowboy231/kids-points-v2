# 儿童积分看板 Kanban (v0.2, 业务=积分)

> 项目: kids-points 积分 dashboard, 1 块桌面 (¥190 P2 128×96) + 挂墙预留 (M2+)
> 交付: 下周二 2026-06-16 (M1 端到端) | 更新: 2026-06-12 (M0.5)
> 完整设计: `docs/plan.md`

---

## 🎯 3 个目标 (本轮 2026-06-12 收窄)

1. **桌面 dashboard 端到端跑通 (下周二 6/16)** — 改 balance.json → 板立即更新 (<1s)
2. **挂墙屏预留** — M2+ 实施, 不阻塞 M1
3. **软件架构稳** — 双保险 (5min 拉 + WS 推), 推失败不影响主

**业务范围**: 只展示积分, V1 kids-points `balance.json` 只读.

---

## ✅ Done (已完成)

- [x] 5 种显示技术对比, 排除 LCD / 投影 / e-ink / CRT / 单色 LCD
- [x] 选定 LED 矩阵 + 反射式护眼 (黑底 + 琥珀 + 关蓝)
- [x] 选定 ESP32-WROOM-32 + HUB75E (非 Pi)
- [x] 选定 DIY 单元板 (非强力巨彩 Q 系列)
- [x] 选定 ¥190 P2 128×96 单元板做桌面 (闲鱼已下单)
- [x] 选定 P2 320×160 × 4 块 1×4 做挂墙 (M2+)
- [x] 架构定: HTTP 拉 (主) + WebSocket 推 (备) 双保险
- [x] 项目文件夹建好 + 持久化
- [x] 范围收窄: 业务 = 积分 (本轮)
- [x] 数据源定: V1 balance.json (本轮, 只读)
- [x] 推送触发定: inotify 监听 V1 文件 (本轮)
- [x] 完整设计文档 `docs/plan.md` (本轮)

---

## 🔄 In Progress (M0.5 范围确认 + 设计, 本轮)

- [x] 完整设计文档 `docs/plan.md` v0.2 (本轮)
- [x] 范围收窄: 业务 = 积分 (本轮)
- [x] 飞书云文档创建: https://test-dgrzdllex625.feishu.cn/docx/UcvcdCRK1oKW2zxwEFQcChlzn6e (本轮)
- [x] 老王答 4 必答中 3 个 (Q2.1/Q3.1/Q3.2/Q7.x) - 仅剩 Q4.1 板到货日
- [ ] 老王拍板 "可以开干 M1" → 启动 M1.1 仿真

---

## 📋 Backlog (按里程碑排序)

### M1: 桌面 dashboard 端到端 (估 06-16, 业务=积分)

#### M1.1 仿真先行 (0 烧录, 0 风险) — 估 06-12 → 06-13

- [ ] **写 `code/sim/led_sim_4zone.py`** — pygame 模拟 128×96 像素, 4 区布局
  - 顶: 标题 12px
  - 中: 3 行流水 8px
  - 底: 今日 + 总积分 10px
  - 黑底 + 琥珀 + 关蓝
- [ ] **准备仿真数据** — `code/sim/sample_balance.json` (含 3-5 条 history)
- [ ] **跑仿真** — `python3 code/sim/led_sim_4zone.py` 看视觉
- [ ] **老王拍板** — 字号/颜色/布局 OK? 改完 0 成本

#### M1.2 Python server (Flask + WS + inotify + systemd) — 估 06-13 → 06-14

- [ ] **写 `code/server/server.py`** — 4 个端点
  - `GET /api/dashboard` — 返 V1 解析后的 JSON (schema 见 plan.md §4)
  - `POST /api/push` — 手动触发推 (老王用 curl)
  - `WS /ws` — 推 `{"action": "refresh"}` 给 ESP32
  - `GET /api/health` — 健康检查
- [ ] **inotify watcher** — `watchdog` 监听 V1 `balance.json` → 触发内存刷新 + WS 推
  - 路径 configurable (env `V1_BALANCE_PATH`, 默认 V1 默认路径)
- [ ] **本地缓存兜底** — 内存 + 磁盘 (`/var/lib/dashboard/cache.json`), V1 文件损坏时用缓存
- [ ] **systemd 单元文件** — `/etc/systemd/system/dashboard.service`
  - 7×24 自启, 失败 3 次重启
  - `journalctl -u dashboard -f` 看日志
- [ ] **端口检查** — `ss -tlnp | grep 8080`, 占用改 8088/9000
- [ ] **本地验证** — `curl http://localhost:8080/api/dashboard` 看 JSON

#### M1.3 ESP32 main.ino (HUB75 + WiFi + 4 区渲染 + WS 收) — 估 06-14 → 06-15

- [ ] **改 `code/esp32/desktop/desktop-dashboard.ino`** — 4 区布局实现
  - 顶: `drawTitle("KID POINTS")` 12px
  - 中: `drawRecent([3 entries])` 8px
  - 底: `drawFooter(todayNet, totalBalance)` 10px
- [ ] **HTTP 拉** — 5min 一次 `GET /api/dashboard`, 解析, 渲染
- [ ] **WS 收** — 连 `ws://<server>:8080/ws`, 收 `refresh` 立即拉
- [ ] **本地缓存** — RAM 存 last good payload, 网络挂渲染 last good
- [ ] **关蓝通道** — `pixel = (r, g, 0)`, 蓝光 = 0
- [ ] **OTA 升级** — `ArduinoOTA` + 浏览器 `http://<esp32>/update` 上传 .bin
- [ ] **Arduino IDE 编译验证** — 库 mrcodetastic/ESP32-HUB75-MatrixPanel-DMA + ArduinoJson + ESPAsyncWebServer + AsyncTCP

#### M1.4 桌面端首次烧录 (板到货后) — 估 06-15

- [ ] **5 分钟验货** (待写 `docs/hardware.md`)
  - USB-C 供电, 板显示测试图 (卖家发来)
  - HUB75 接口检查, 坏点位置记录
- [ ] **首次 USB 烧录** — Arduino IDE → Tools → Port → /dev/ttyUSB0 → Upload
- [ ] **Wi-Fi 配网** — 写死 SSID/密码 (Q3.1/Q3.2 答了之后)
- [ ] **服务器 IP 配** — 写死 IP (Q2.1 答了之后)
- [ ] **板显示静态** — 验证 HTTP 拉取链路通
- [ ] **WS 推验证** — 板端 WS 连上, 服务器侧触发推, 板 <1s 更新

#### M1.5 端到端验证 — 估 06-15 → 06-16

- [ ] **改 V1 balance.json** — 手动加一条记录 (模拟用户操作)
- [ ] **< 1s 更新** — 板立即显示新流水
- [ ] **5min 兜底** — 关掉 inotify, 等 5min, 板也能拉
- [ ] **网络断** — 拔服务器网线, 板显示 last good, 不白屏
- [ ] **恢复** — 插回网线, 板 <5min 内恢复
- [ ] **24h 稳定性** — 跑 1 整天, 看 systemd 日志无 OOM / 内存泄漏

### M2: 挂墙屏 (4 块 P2 320×160 × 1×4) — 估 6/20+, 不阻塞 M1

- [ ] **采购 4 块 P2 320×160 单元板** — 1 块带 ESP32, 3 块不带
- [ ] **采购 5V 8A 电源** + 电源分配板
- [ ] **采购 HUB75 16P 排线 × 5** (1 主 → 4 屏菊花链)
- [ ] **采购外壳材料** — 50" 8:1 横幅 (铝型材/木框, 待 Q6 答)
- [ ] **ESP32 端 4 屏级联 main.ino** — chain=4, 640×80 像素 (1×4 拼接) 或 320×160 像素 (2×2 拼接, 待定)
- [ ] **HUB75 菊花链接线** — 屏1 OUT → 屏2 IN → 屏3 IN → 屏4 IN
- [ ] **首次烧录 + 配网**
- [ ] **拉取验证** — 4 屏显示静态内容
- [ ] **亮度均匀性** — 4 屏色温/亮度校准 (同批次 + 软件伽马)
- [ ] **挂墙外壳组装 + 挂架**

### M3+: 优化 (估 7 月起, 不阻塞 M1/M2)

- [ ] 夜间模式 (cron 0:00-6:00 降到 20% 亮度)
- [ ] 字体升级 (8px → 12px / 16px 易读)
- [ ] 长内容滚动 (流水 description 超 12 字符滚动)
- [ ] OTA 流程文档化
- [ ] Web 录入页 (M7 可选, 不一定做)
- [ ] 天气/日历 (M7 可选, 不一定做)
- [ ] 倒计时 (M7 可选, 不一定做)

---

## ❓ Blocking (等老王回答, 详见 `notes.md` 🔴)

M1.4 烧录/部署前必答:
- [x] ✅ **Q2.1**: Linux 服务器 IP = `YOUR_SERVER_IP` (自查 `ip addr` + `ping` 0.014ms 确认, 无线网卡 `wlp0s20f3`, 网关 192.168.50.1)
- [x] ✅ **Q3.1 / Q3.2**: Wi-Fi SSID = `Asur737` / 密码 = `q2lrLIvUs` (2.4GHz 兼容)
- [ ] ❓ **Q4.1**: ¥190 板预计到货日 (老王手动通知, 板到即解锁 M1.4)
- [x] ✅ **Q7.x**: 看板标题 = `Kid Dashboard`

**当前状态**: 4 必答 3 已答, 仅剩 Q4.1 板到货日. M1.1 / M1.2 / M1.3 (仿真/Python/ESP32 代码) 今起可开干, 0 阻塞.

---

## 📊 风险 (老王要知道的)

| 风险 | 影响 | 缓解 | 状态 |
|---|---|---|---|
| ¥190 闲鱼板是二手, 到货可能有问题 | M1.4 延后 | 已确认卖家全好, 退换货 OK | 🟡 |
| 4 块 P2 320×160 没准现货 (M2) | M2 延后 3-5 天 | 多看 2-3 卖家, 1688 备选 | 🟢 (M2) |
| 4 屏级联 HUB75 接线错位 (M2) | M2 调试多花 1-2 天 | 先 1 屏调通, 再级联 | 🟢 (M2) |
| 4 屏色温/亮度不均 (M2) | M2 视觉效果差 | 同批次买 + 软件伽马校正 | 🟢 (M2) |
| Flask 后台挂 | 看板白屏 | systemd 自启 + 本地缓存兜底 | 🟡 M1.2 实施 |
| inotify 在 sandbox/容器不通 | 推失效 | 退化到 5min 轮询 (主路径仍工作) | 🟡 M1.2 验证 |
| Flask 端口冲突 | 起不来 | 先查, 不通改 8088/9000 | 🟢 |
| 中文字体 8px 在 128px 宽挤 | 流水行超宽 | 截断到 12 字符 + M3 滚动 | 🟢 |
| 网络抖动 (Wi-Fi 抖) | WS 推失败 | 5min 轮询兜底, ESP32 自动重连 WS | 🟢 |
| kids-points 漏扣 (V1 5/19 之前 11 条) | 显示数字与 V1 历史对不上 | 不修复 (V1 永不动), 文档说明 | 🟢 |
| ¥190 板 6/16 不到 | M1.4 烧录延期 | M1.1-M1.3 全部完成, 板到即烧, M1.5 周末/下周三补 | 🟡 老王必答 Q4.1 |
| V1 schema 改 | dashboard 解析失败 | 单点 adapter, V1 字段变化一处改 | 🟢 |
| **老王额度空档** (本轮 0 任务执行) | M1.1 起所有任务 | 等老王拍板"开始 M1"再执行 | 🟡 当前状态 |

---

## 📅 时间线 (下周二 6/16 视角)

```
06-12 (今天) ──────────────────── M0.5 完成 (本轮)
  ↓ 老王拍板 "可以开干"
06-12 → 06-13  M1.1 仿真 (0 烧录, 0 风险) ─── 老王额度空档优先跑
  ↓
06-13 → 06-14  M1.2 Python server ───── 老王额度空档跑
  ↓
06-14 → 06-15  M1.3 ESP32 写代码 ─────── 老王额度空档跑
  ↓
06-15 (板到货日, Q4.1) → M1.4 USB 烧录
  ↓
06-15 → 06-16  M1.5 端到端验证 ─────── 老王额度空档跑
  ↓
06-16  M1 完成, 桌面 dashboard 端到端跑通 ✅
  ↓
06-20+  M2 挂墙屏 (不阻塞)
```

**关键路径**: M1.1 (仿真) → M1.2 (Python) → M1.3 (ESP32) → M1.4 (烧录, 需板+IP+Wi-Fi) → M1.5 (验证)

**老王 Q&A 答完** (IP/Wi-Fi/板到货日/标题) → M1.4 可启动.
**仿真先行** → 即使板不到, M1.1-M1.3 全部完成, 0 风险.
