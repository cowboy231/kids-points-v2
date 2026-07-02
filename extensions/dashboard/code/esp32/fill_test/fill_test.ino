// v26: v25 配法 + 文字测试 (字号 2, 跟店家 HUB75E.txt L48 setTextSize(2) 一致)
//  v25 修好 (整屏 1 色 fillScreen 循环)
//  v26 验证: 字号 2 文字能不能在屏上正确显示
//  配法 = v2.0.7 店家伙 100% 复刻

#include <ESP32-VirtualMatrixPanel-I2S-DMA.h>

#define PANEL_RES_X 96
#define PANEL_RES_Y 64
#define PIN_E 16
#define NUM_ROWS 2
#define NUM_COLS 1
#define PANEL_CHAIN NUM_ROWS*NUM_COLS
#define SERPENT false
#define TOPDOWN false

MatrixPanel_I2S_DMA *dma_display = nullptr;
VirtualMatrixPanel  *virtualDisp = nullptr;

int bright_ness = 80;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== fill_test v26 (2026-06-19) - 文字测试, 字号 2 (跟店家一致) ===");

  HUB75_I2S_CFG mxconfig(PANEL_RES_X, PANEL_RES_Y, PANEL_CHAIN);
  mxconfig.gpio.e = PIN_E;
  dma_display = new MatrixPanel_I2S_DMA(mxconfig);
  dma_display->setBrightness8(bright_ness);
  if (not dma_display->begin()) {
    Serial.println("KABOOM!"); while (true) delay(1000);
  }
  virtualDisp = new VirtualMatrixPanel(
    (*dma_display), NUM_ROWS, NUM_COLS,
    PANEL_RES_X, PANEL_RES_Y, SERPENT, TOPDOWN
  );
  virtualDisp->fillScreen(virtualDisp->color444(0, 0, 0));
  Serial.println("[init] ready");
}

void loop() {
  // 字号 2 (店家 HUB75E.txt 用这个) 文字 HELLO
  virtualDisp->fillScreen(virtualDisp->color444(0, 0, 0));
  virtualDisp->setTextSize(2);
  virtualDisp->setTextColor(virtualDisp->color444(15, 0, 0));  // RED
  virtualDisp->setCursor(0, 0);
  virtualDisp->print("HELLO");
  Serial.println("[loop] HELLO size=2 RED");
  delay(3000);

  virtualDisp->fillScreen(virtualDisp->color444(0, 0, 0));
  virtualDisp->setTextSize(2);
  virtualDisp->setTextColor(virtualDisp->color444(0, 15, 0));  // GREEN
  virtualDisp->setCursor(0, 0);
  virtualDisp->print("WORLD");
  Serial.println("[loop] WORLD size=2 GREEN");
  delay(3000);

  virtualDisp->fillScreen(virtualDisp->color444(0, 0, 0));
  virtualDisp->setTextSize(2);
  virtualDisp->setTextColor(virtualDisp->color444(15, 15, 0));  // YELLOW
  virtualDisp->setCursor(0, 0);
  virtualDisp->print("75.5");
  Serial.println("[loop] 75.5 size=2 YELLOW");
  delay(3000);

  // 字号 1 小字
  virtualDisp->fillScreen(virtualDisp->color444(0, 0, 0));
  virtualDisp->setTextSize(1);
  virtualDisp->setTextColor(virtualDisp->color444(0, 15, 15));  // CYAN
  virtualDisp->setCursor(0, 0);
  virtualDisp->print("KIDS POINTS");
  Serial.println("[loop] KIDS POINTS size=1 CYAN");
  delay(3000);
}
