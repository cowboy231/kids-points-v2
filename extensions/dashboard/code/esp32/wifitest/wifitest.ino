#include <WiFi.h>
// 最简 WiFi scan — 看 ESP32 能否扫到 SSID
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== WiFi Scan Test ===");
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  int n = WiFi.scanNetworks();
  Serial.printf("scan done: %d networks\n", n);
  for (int i = 0; i < n; i++) {
    Serial.printf("  %d: %s (%d dBm) %s\n",
      i+1, WiFi.SSID(i).c_str(), WiFi.RSSI(i),
      WiFi.encryptionType(i) == WIFI_AUTH_OPEN ? "open" : "enc");
  }
  Serial.println("\n=== 现在连 YOUR_WIFI_SSID ===");
  WiFi.begin("YOUR_WIFI_SSID", "YOUR_WIFI_PASSWORD");
  for (int i = 0; i < 50; i++) {
    delay(200);
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("连上! IP=%s\n", WiFi.localIP().toString().c_str());
      break;
    }
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.printf("10s 后仍未连上, status=%d\n", WiFi.status());
  }
}

void loop() { delay(1000); }
