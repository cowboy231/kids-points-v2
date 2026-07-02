# 后续路线图 (M1.5+)

## ✅ M1.4 完成 (2026-06-19)

- ESP32 + HUB75 96×128 跑通
- v4.9: 5 行流水 + 智能渲染
- 老王决策归档 (见 README.md "老王决策")

---

## 🔴 M1.5 优先级最高 (本周内)

### 1. server systemd 开机自启
- ✅ service 文件已有: `/home/wang/projects/kids-points-v2/extensions/dashboard/code/server/dashboard.service`
- ❌ 未 enable + start
- 步骤:
  ```bash
  sudo cp /home/wang/projects/kids-points-v2/extensions/dashboard/code/server/dashboard.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now dashboard
  sudo systemctl status dashboard
  ```

### 2. 亮度调整 (BRIGHTNESS=255 过曝)
- 当前 255 (拍照片调试用)
- 室内日用建议 **80-120** (esp32 全暗=0, 最亮=255)
- 改 `const uint8_t BRIGHTNESS = 100;` 然后重烧

### 3. 修 today_net bug (显示 +10 实际 = 0)
- 现象: server 返 `today_net=10`, 但今日实际无 +10 交易
- 根因 (推测): V2 CLI `today` 子命令的 `net` 字段计算 bug
- **最新观察** (2026-06-19): server 返 `today_count=0, today_net=0`, 正确 → bug 可能已自愈, **需要确认** 老王今日无交易还是修复了
- 修复: 查 `/home/wang/projects/kids-points-v2/runtime/cli.py today` 实现

---

## 🟡 M1.6 体验优化 (2 周内)

### 4. 加按键 / 翻页
- ESP32 用 2 个 GPIO 接按钮 (上 / 下)
- 加 1 行状态栏: `PG 1/3` 显示当前页
- 当前页 (近 5 条) → 历史页 (5-10 条) → 趋势页 (周/月汇总)

### 5. 加闪烁 / 颜色状态
- 当前正积分 (今天) → 绿色 (+)
- 当前负积分 (今天) → 红色 (-)
- 中性 → 琥珀 (默认)

### 6. 节假日 / 生日特效
- 检测日期 → 屏显示 🎂 (像素风)
- 万圣节 / 春节特殊主题

---

## 🟢 M2.0 架构升级 (1 个月内)

### 7. in-memory cache (v5.4 完成, 取代 WS 推)
- 之前: ES p32 每 5s 拉 + watchdog WS 推 (ESP32 不收, 僵尸代码)
- 现状 (v5.4): watchdog 监听 V2 SQLite → 标 in-memory cache dirty → 下次 GET 时 fetch
  - 99% 请求走 cache (V2 没写就 0 subprocess)
  - V2 挂掉时屏显示最后正常数据
  - subprocess 调用: 720/小时 → 每天几次
- **决策**: ✅ 已完成, 不再需要 WS

### 8. OTA 远程升级
- 现状: 关 (省 RAM, I2S DMA 稳跑)
- 改进: 加 AsyncElegantOTA (ESP32 库, ~10KB Flash)
- 收益: 不用 USB 烧录
- **决策**: 桌面板子 USB 烧录 1 分钟, **不做**

### 9. 多屏支持
- 现状: 单屏
- 改进: server 加 `screen_id` 路由, ESP32 加 `SCREEN_ID` 常量
- 应用: 儿童房 / 客厅 / 厨房各放 1 块

### 10. 家长手机 App / Web 控制
- Web UI: 加 Flask 路由 `/admin`, HTML 表单
- 加积分 / 减积分 / 设目标 / 看历史
- 替代 V2 CLI 命令行, 适合非技术家长

---

## 🔵 M3.0+ 长期愿景 (3 个月+)

### 11. 其他场景接入
- 体重秤 / 血压计数据
- 番茄钟 / 学习计时
- 天气 / 日程
- 家庭成员状态 (在家 / 出门)

### 12. AI 加成
- LLM 自动评价 (今天孩子表现 → 文字点评)
- 自动奖励检测 (学习完成 → 自动 +5)
- 语音播报 (ESP32 加 MAX98357A I2S 功放, 复用 I2S 引脚要小心)

### 13. 多端协同
- ESP32 端 → BLE 连接手机 (推送通知)
- 平板端 (iPad / Android) → 同步显示
- Apple Watch / 手环 → 实时积分变化

---

## 优先级决策原则

按 **老王决策风格** (USER profile):
1. **够用就好不冒险升级** (06-19): 6h+ 烧录后老王质疑升级 v3.0.14, 选 v2.0.7 → M2.0/3.0 慎做
2. **业务效果优先, 技术术语后置** (06-19): 跟老王沟通用"屏不闪"而不是"memcmp 智能渲染" → 优先级讨论也用业务语言
3. **多件小修复一次做完** (协作偏好) → M1.5 三件事 (systemd + 亮度 + bug) 一起推

---

## 本周冲刺 (老王确认后开干)

```
✅ M1.5-1 systemd enable+start        (5 分钟)
✅ M1.5-2 亮度 100                    (改代码 + 重烧, 5 分钟)
✅ M1.5-3 修 today_net bug 调查       (查 V2 CLI, 15 分钟)
✅ 拍 v4.9 验证照片归档               (5 分钟)
```

总耗时 ~30 分钟, **等老王一句话"开干"**。