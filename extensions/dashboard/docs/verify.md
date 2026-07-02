# 验证手册 + FAQ

## 快速验证 (30 秒)

### 1. 服务端跑着
```bash
curl http://YOUR_SERVER_IP:8080/api/health
# {"status": "ok", ...}

curl http://YOUR_SERVER_IP:8080/api/dashboard | python3 -m json.tool
# 看 title / total_balance / recent 是否符合预期
```

### 2. ESP32 跑着
```bash
# 串口日志
arduino-cli monitor -p /dev/ttyUSB0 -c baudrate=115200
# 期望看到:
# [v2.7] WiFi 连上, IP=192.168.50.197
# [fetch] OK: balance=77, today_count=0, today_net=0, recent=5
```

### 3. 屏显示正确
按 EN 复位 ESP32, 看屏:
- 标题 "KID POINTS" 顶部
- 横线 1
- 5 行流水 (e.g. `+2 口算题` / `+3 跳绳` / `-5 看动画片` / ...)
- 横线 2
- 底栏 `T+0 ALL:77` 或 `T-- ALL:77` (today_count=0 时显示 T--)

---

## FAQ

### Q1: 屏不亮 / 全黑
**A**:
1. 电源 5V 4A 接了吗? ESP32 USB 单独供电?
2. HUB75 排线插紧了吗?
3. ESP32 串口有日志吗? 没有 → 死机, 完全拔 USB 30s+
4. 有日志但屏不亮 → 库版本错配, 用 v2.0.7 + `mxconfig.gpio.e = 16`

### Q2: 屏花屏 / 颜色错
**A**:
1. E pin 接了吗? (1/32 扫必须有)
2. 跑 fill_test.ino 看色块是否对得上物理位置
3. 改 `mxconfig.gpio.e = 16` 强制 (即使默认是 -1)

### Q3: WiFi 连不上
**A**:
1. NVS 丢了? 烧 wifitest 重建 (见 pitfalls.md #1)
2. 密码对吗? 核对 `WIFI_PASS` 常量
3. 2.4G vs 5G? ESP32 只支持 2.4G
4. 信号弱? 把 ESP32 靠近路由器 1 米

### Q4: HTTP fetch 失败
**A**:
1. server 跑着吗? `curl http://YOUR_SERVER_IP:8080/api/health`
2. IP 对吗? 改 `SERVER_HOST` 常量
3. ESP32 / server 在同一网段? ESP32 用 WiFi, server 用有线, 要路由通
4. 串口日志: `[fetch] HTTP 500` → server 返错; `JSON parse 失败` → schema 不匹配

### Q5: 字符乱码 / 方块
**A**:
1. 字库选 gb2312b (v4.7), 不要 chinese3
2. 看 description 是不是 UTF-8 (V2 CLI 默认是)
3. 罕见字 (GB2312 一级字库 90% 覆盖), 二级字库需自造 fontforge

### Q6: 数字跟中文 baseline 不齐
**A**:
1. 全 U8g2 接管 (不要 GFX 5×7 + U8g2 混)
2. 数字 7x13_tr + 中文 gb2312b, 字符高都 13 → 自动对齐
3. 见 v4.0 / v4.2 决策 (esp32-code.md)

### Q6.5: 颜色看着不对 / 不鲜艳 (v4-v5.0 bug, v5.1 修复)
**A**:
1. v5.0 之前 `COLOR_AMBER = 0xFF8C00` 是 RGB888, 库取低 16 位 = `0x8C00` (偏绿黄)
2. v5.1 改用真 RGB565 `0xFC40` (真琥珀)
3. 板子是 RGB 全彩, 可显示红/绿/蓝任意色, v5.1 起启用全彩

### Q7: 屏闪 (数据没变也重画)
**A**:
1. 升级到 v4.8 智能渲染 (memcmp 比对)
2. 5s 拉 + memcmp → 数据没变 return → 静默
3. 见 pitfalls.md #12

### Q8: 只显示 3 行流水, 想 5 行
**A**:
1. 升级到 v4.9 (`recent[3]` → `recent[5]`)
2. 改 `data_source.py` 的 `--days 1 --limit 3` → `--days 7 --limit 5`
3. 加 `ROW_4_Y=78` / `ROW_5_Y=94` 布局

### Q9: 烧完串口没日志
**A**:
1. 按 ESP32 板 EN 按钮 (手动复位)
2. esptool 烧完不重启 ESP32
3. 见 pitfalls.md #10

### Q10: 烧录失败 / esptool 报 "Failed to connect"
**A**:
1. ESP32 进 boot 模式? 按住 BOOT 按钮 + EN 按钮, 松开 EN, 再松开 BOOT
2. USB 线是数据线还是只供电? 换数据线
3. `/dev/ttyUSB0` 权限? `sudo chmod 666 /dev/ttyUSB0`
4. CH340 死锁? 完全拔 USB 30s+

### Q11: 编译报错 "库找不到"
**A**:
```bash
arduino-cli lib install "ESP32 HUB75 LED MATRIX PANEL DMA Display"
arduino-cli lib install "U8g2 for Adafruit GFX"
arduino-cli lib install "ArduinoJson"
arduino-cli lib install "Adafruit GFX Library"
```

### Q12: 烧完 NVS 丢了 / WiFi 密码丢
**A**: 见 pitfalls.md #1, 烧 wifitest 重建
```bash
arduino-cli compile --fqbn esp32:esp32:esp32 /home/wang/projects/kids-points-v2/extensions/dashboard/code/esp32/wifitest
esptool --chip esp32 --port /dev/ttyUSB0 --baud 921600 \
  write_flash 0x10000 /home/wang/projects/kids-points-v2/extensions/dashboard/code/esp32/wifitest/wifitest.ino.bin
```

### Q13: server 起不来 / 端口占用
**A**:
```bash
# 看谁占着 8080
sudo lsof -i :8080
# 或
sudo ss -tlnp | grep 8080

# 杀老 server
pkill -f "server.py"
# 等 3 秒, 端口释放
# 再启动新 server
cd /home/wang/projects/kids-points-v2/extensions/dashboard/code/server && nohup python3 server.py > /tmp/dashboard.log 2>&1 &
```

### Q14: today_net 显示 +10 但实际 = 0
**A**: 
- **最新** (2026-06-19): server 返 `today_count=0, today_net=0` 正确 → 可能已自愈
- 如果仍错: 查 V2 CLI `cli.py today` 实现, 或在 `data_source.fetch_data()` 里手动按 recent 重算
- 见 roadmap.md M1.5-3

### Q15: 屏亮度太亮 / 太暗
**A**:
改 `const uint8_t BRIGHTNESS = 50;` (当前 50, v5.3 老王决策), 重烧。
- 0 = 全暗
- 50 = **夜间 / 室内柔和 (当前, v5.3 老王决策)**
- 70 = 室内 (v5.2, 老王嫌仍偏亮 → 50)
- 100 = 室内日用
- 150 = 日光
- 255 = 拍照

### Q15.5: 底栏 "今日" / "总分" 数字位常变 (v5.3 老王决策)
**A**:
- 数字格式固定 3 字符宽 (`%+3d` / `%3d`), 即使 +0 跟 +10 跟 +100, 占位都不跳
- 底栏 label 缩成 "今" + "总" (省 24 px) 抵消新加的 14 px 间隙
- 效果: 屏上 `今  +5          总  77`, 数字位置稳定

### Q16: 蓝光护眼红线 (老王 2026-06-19 决策)
**A**:
1. **永久禁止任何含蓝光的颜色** (LED 蓝光波长 ~470nm 直接伤眼)
2. RGB565 B 通道 = 低 5 bit (`0x001F`)
3. 调色板全部 B=0 (零蓝光: 琥珀/红/绿/黑)
4. **编译期硬检查**: 任一常量含 B>0 → 编译失败 (`#error`)
5. 未来加颜色必须 `HAS_BLUE(color) == 0`, 否则编译报错
6. 禁用颜色: 蓝 / 紫 / 粉 / 白 (任何含 B>0)

需要蓝光颜色时必须先跟老王讨论护眼取舍.

---

## 性能指标 (期望值)

| 指标 | 值 | 验证方法 |
|------|-----|----------|
| 启动到屏显示 | < 5s | 串口日志 `BOOT v4.8` 到第一次 `render_frame()` |
| WiFi 连接时间 | 2-5s | 串口日志 |
| 第一次 fetch 时间 | < 200ms | 串口日志 `[fetch] OK` |
| fetch 间隔 | 5s | 看串口日志间隔 |
| render 间隔 | 5s | 同上 |
| memcmp 比对 | < 1μs | 几乎不可测 |
| 5 行重画总时间 | ~50ms | 实测 |
| Flash 占用 | 1049 KB / 1310 KB (80%) | `arduino-cli compile` 输出 |
| RAM 占用 | 47 KB / 320 KB (14%) | `ESP.getFreeHeap()` 串口日志 |
| CPU 占用 | < 2% | 空闲 loop 99% 时间在 delay |
| WiFi 占用率 | < 1% | 设计寿命 MTBF > 50万小时 |

---

## 故障排查决策树

```
屏不工作
├─ 上电无反应 (无串口日志, 屏不亮)
│  ├─ 电源问题? → 检查 5V 4A + USB
│  ├─ ESP32 死机? → 完全拔 30s+
│  └─ 烧录错? → 重烧 (esptool 0x10000 + 按 EN)
│
├─ 上电有日志 (串口有 print) 但屏不亮
│  ├─ HUB75 排线松? → 重插
│  ├─ 库版本错? → 用 v2.0.7 + 强制 e=16
│  └─ I2S KABOOM? → 关 WebServer/OTA/WS
│
├─ 屏亮但内容错 (花屏 / 颜色错)
│  ├─ E pin 没接? → 接 Pin 16
│  ├─ pinmap 错? → 核对店家 HUB75E.txt
│  └─ fill_test 验证 → 跑 fill_test.ino 看色块位置
│
├─ 内容对但 layout 错 (重叠 / 溢出)
│  ├─ 中文 12×13 baseline? → 全 U8g2 接管
│  ├─ 行间距? → 改 ROW_X_Y 常量
│  └─ 屏宽装不下? → 改字号 / 切 description
│
└─ 显示正确但行为错 (闪 / 不更新)
   ├─ 屏闪? → 升 v4.8 memcmp 智能渲染
   ├─ 数据不更新? → curl /api/dashboard 看 server 数据
   ├─ server 不更新? → 看 V2 CLI 直跑结果
   └─ V2 CLI 不对? → 查 kids_points.db 内容
```

---

## 联系 / 求助

- 老王 → `wangmouren.online` 履历 + 飞书 IM
- 项目根目录: `/home/wang/projects/kids-points-v2/extensions/dashboard/`
- 项目 docs: `/home/wang/projects/kids-points-v2/extensions/dashboard/docs/`
- 代码: `/home/wang/projects/kids-points-v2/extensions/dashboard/code/`
- 数据: V2 CLI 内部 (StuAgent 项目)