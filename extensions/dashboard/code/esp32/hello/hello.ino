// 最简 hello.ino - 验证烧录链路 (0 依赖 HUB75)
// 2026-06-18 老王怀疑烧录没上, 写最简 .ino 验证
// 期望: Serial.println 输出 "HELLO FROM ESP32" + 每秒 "LOOP"

void setup() {
  Serial.begin(115200);
  delay(2000);  // 给 ESP32 boot 时间
  Serial.println("");
  Serial.println("=== HELLO FROM ESP32 ===");
  Serial.println("If you see this, flash + Serial work!");
  Serial.println("If 0 output, ESP32 dead or flash broken");
}

void loop() {
  Serial.println("LOOP");
  delay(1000);
}
