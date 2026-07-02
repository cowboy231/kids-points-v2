// =============================================================
// 挂墙结算展示屏 - 4 块 P2 320×160 × 1×4 横拼 (50" 8:1 横幅)
// =============================================================
// 状态: 骨架, 待 M3-M5 实施
//
// 物理: 1280×160mm
// 像素: 640×80 (4 块 × 160×80 / 块)
// 硬件: 1 块 P2 320×160 + ESP32 HUB75E (主控)
//       3 块 P2 320×160 (从, 无 ESP32)
// 接线: 菊花链, 屏1 OUT → 屏2 IN → 屏3 IN → 屏4 IN
// =============================================================

#include <Arduino.h>
// (库同 desktop)

// ---- CONFIG ----
const char* WIFI_SSID  = "TODO_FILL";
const char* WIFI_PASS  = "TODO_FILL";
const char* SERVER_URL = "http://TODO_FILL:8080/api/dashboard";
const unsigned long FETCH_INTERVAL_MS = 30000;
const uint8_t BRIGHTNESS = 70;  // 0-255, 挂墙远看 70 即可

// ---- HUB75 config (4 块级联) ----
// HUB75_I2S_CFG mxconfig(160, 80, 4);  // 单块 160×80, chain=4 = 640×80 总
// MatrixPanel_I2S_DMA *dma_display = nullptr;

void setup() {
  Serial.begin(115200);
  // TODO: HUB75 初始化 (chain=4)
  // TODO: 伽马校正 (4 屏色温统一)
  // TODO: WiFi + OTA + WebSocket
}

void loop() {
  // TODO: 30s 拉
  // TODO: 渲染 (横幅布局, 长内容滚动)
  // TODO: 夜间模式 (低亮度)
}
