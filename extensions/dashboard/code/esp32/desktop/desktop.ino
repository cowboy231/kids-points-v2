// =============================================================
// 桌面 dashboard - P2 96×64 单元板 × 2 块链 = 96×128
// M1.4 v5.3 (2026-06-20) — 亮度 50 + 底栏位稳定
//
// v5.3 关键改动 (相对 v5.2):
//  - BRIGHTNESS 70 → 50 (老王决策, 再降一档更柔和)
//  - 底栏 "今日"→"今" + "总分"→"总" (省 24 px 抵消新间隙)
//  - today_buf 格式 %+d → %+3d (固定 3 字符宽, 数字位稳定不再跳)
//  - total_buf 格式 %d → %3d (固定 3 字符宽, 对称)
//  - 加 2 数字位空格 (14 px) 改善视觉间隔 (老王: 70 仍偏亮, 50 更柔和;
//    今日跟总分挤, 数字位常变; 缩中文 + 占位解决)
//
// v5.2 关键改动 (相对 v5.1):
//  - BRIGHTNESS 100 → 70 (老王决策, 更柔和室内)
//  - 加蓝光护眼硬红线 (编译期 #error 硬检查)
//    老王 2026-06-19 决策: 永久禁止任何含蓝光的颜色
//    RGB565 B 通道 = 低 5 bit (0x001F)
//    调色板全部 B=0 (零蓝光), 未来加蓝光颜色编译会失败
//    当前调色板: 琥珀/红/绿/黑 (全部护眼, 跟 v4 琥珀一样)
//
// 数据流: (跟 v4.9 一致)
//   Flask GET /api/dashboard  ← 5s 拉 1 次 (智能渲染: 数据没变不重画)
//   RAM 缓存 last_good  ← 网络挂时显示
// =============================================================

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
// v2.0: 改用 v2.0.7 店家伙 (ESP32-VirtualMatrixPanel-I2S-DMA.h, 实际是 ESP32-HUB75-MatrixPanel-I2S-DMA.h)
#include <ESP32-VirtualMatrixPanel-I2S-DMA.h>
// v4.0: 删 AsyncWebServer/AsyncTCP/ArduinoOTA (v2.7 已不用, 只留 fetch, 编译省 36KB RAM + I2S DMA 才能跑)
#include <U8g2_for_Adafruit_GFX.h>  // v1.1 加: 中文桥接

// ---- CONFIG (跟 v1.1 一致, M1.4 烧录前老王核对 1 次密码) ----
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASS     = "YOUR_WIFI_PASSWORD";
const char* SERVER_HOST   = "YOUR_SERVER_IP";      // D16, Linux 服务器
const uint16_t SERVER_PORT = 8080;                  // 跟 M1.2 server.py 一致
const unsigned long FETCH_INTERVAL_MS = 5000;       // v4.8: 30s → 5s (智能渲染后拉频繁没关系, 数据没变不重画)
const uint8_t BRIGHTNESS  = 50;                    // v5.3: 70 → 50 (老王决策, 再降一档更柔和)
const char* DASHBOARD_TITLE = "KID POINTS";         // 跟 v1.1 一致

// ---- v2.0: 物理参数 (店家 HUB75E.txt 100% 复刻) ----
// 96×64 单元板 × chain=2 拼 96×128 (vertical 96 宽 × 128 高)
#define PANEL_RES_X 96
#define PANEL_RES_Y 64
#define PANEL_CHAIN 2   // 2 块链 (96×128)
// v2.0.7 VirtualMatrixPanel 7 参数 (店家 HUB75E.txt L40)
#define NUM_ROWS 2      // 2 块链垂直拼
#define NUM_COLS 1      // 1 列
#define SERPENT  false  // 店家伙配置
#define TOPDOWN  false

// 4 区 y 坐标 (跟 sim/desktop_sim.py ORIENTATION_CONFIGS["vertical"] 1:1, 适配 96×128)
// v4.9 布局 (5 行流水, 行间距 16 px)
//   标题 baseline y=10
//   横线 1 y=15
//   行 1 baseline y=30 (顶部 17)
//   行 2 baseline y=46 (顶部 33, 间距 3px)
//   行 3 baseline y=62 (顶部 49)
//   行 4 baseline y=78 (顶部 65)
//   行 5 baseline y=94 (顶部 81)
//   横线 2 y=108 (底部 y=94, 距横线 14px)
//   底栏 baseline y=125 (顶部 112, 距下边 2px)
#define TITLE_Y       3
#define DIVIDER_1_Y   15
#define ROW_1_Y       30
#define ROW_2_Y       46
#define ROW_3_Y       62
#define ROW_4_Y       78
#define ROW_5_Y       94
#define DIVIDER_2_Y   108
#define FOOTER_Y      125

// v4.2: 全 U8g2 接管, 字号由字体本身决定 (setFont)
//   - 数字: u8g2_font_7x13_tr (字符 7×13 px, 高跟 chinese 13 完全匹配, baseline 完美对齐)
//   - 中文: u8g2_font_wqy12_t_chinese3 (字符 12×13 px, baseline = 字符底部)
//   - 数字 baseline 偏移 +2 (数字底部对齐 chinese3 底部, 顶部悬 2px 反而居中视觉)

// 物理内边距
#define PAD_X 4

// 配色 (真 RGB565, 16-bit, 屏是 RGB 全彩, v5.1 启用)
//   RGB565 格式: RRRRR GGGGGG BBBBB
//   之前 v5.0 用 0xFF8C00 (RGB888) 是错的, 库取低 16 位 = 0x8C00
//   实际显示偏暗绿黄, 不是琥珀. v5.1 改用真 RGB565 重新算
// v5.1 老王决定启用全彩 (之前是单色琥珀是审美选择, 硬件本身是 RGB)
//   颜色区分 (老王决策 B):
//     + → 绿 (正积分, 一眼看出"赚")
//     - → 红 (负积分, 一眼看出"扣")
//     0 → 琥珀 (中性, 跟标题一致)
//
// === v5.2 蓝光护眼硬红线 (老王 2026-06-19 决策) ===
//   儿童看板强调护眼, 老王拍板: 永久禁止任何含蓝光的颜色
//   蓝光伤眼 (LED 蓝光波长 ~470nm, 直接刺激视网膜黄斑)
//   RGB565 B 通道 = 低 5 bit (0x001F)
//   任何含 B>0 的颜色 → 编译直接失败 (见下方 #error 检查)
//   如未来真要加蓝光颜色, 必须先跟老王讨论护眼取舍
//
//   当前调色板全部 B=0 (零蓝光):
//     琥珀 (R+G 混合)  → 0% 蓝光 ✅
//     红 (R only)       → 0% 蓝光 ✅
//     绿 (G only)       → 极低蓝光 (绿 LED 蓝光成分弱) ✅
//     白 (R+G+B 全亮)   → 强蓝光 ❌ (永不加)
//     蓝/紫/粉          → 含蓝光 ❌ (永不加)
#define BLUE_BIT_MASK 0x001F                       // B 通道在 RGB565 的 bit 位
#define HAS_BLUE(color) ((color) & BLUE_BIT_MASK)   // 1 = 含蓝光

#define COLOR_BLACK     0x0000   // B=0 ✅
#define COLOR_AMBER     0xFC40   // B=0 ✅  R=31 G=34 B=0 真正琥珀
#define COLOR_AMBER_DIM 0x4200   // B=0 ✅  暗琥珀 (空行占位/等待)
#define COLOR_GREEN     0x07E0   // B=0 ✅  R=0  G=63 B=0 纯绿 (正 +)
#define COLOR_RED       0xF800   // B=0 ✅  R=31 G=0  B=0 纯红 (负 -)
#define COLOR_RED_ERR   0xC000   // B=0 ✅  暗红 (错误提示, 比纯红柔和)

// 蓝光护眼红线硬检查 (编译期): 任一调色板常量含蓝光 → 编译失败
#if HAS_BLUE(COLOR_BLACK) || HAS_BLUE(COLOR_AMBER) || \
    HAS_BLUE(COLOR_AMBER_DIM) || HAS_BLUE(COLOR_GREEN) || \
    HAS_BLUE(COLOR_RED) || HAS_BLUE(COLOR_RED_ERR)
#error "蓝光护眼红线违反 (老王 2026-06-19 决策): 调色板常量含蓝光 (B>0). RGB565 B 通道 = 低 5 bit (0x001F). 如需用, 先跟老王讨论护眼取舍."
#endif

// ---- v2.0: HUB75 (v2.0.7 店家伙 100% 复刻 HUB75E.txt L25-30) ----
// 默认 pinmap: R1=14 G1=27 B1=26 R2=25 G2=33 B2=32 A=13 B=15 C=2 D=4 E=16 LAT=5 OE=18 CLK=17
// 注意: v2.0.7 库不允许 mxconfig 在全局修改字段, 移到 setup() 里
MatrixPanel_I2S_DMA* dma_display = nullptr;
VirtualMatrixPanel* virtualDisp = nullptr;  // v2.0 新加: 2 块链 virtual display

// ---- v1.1: U8g2 桥接 (中文字体) ----
U8G2_FOR_ADAFRUIT_GFX u8g2;

// ---- 业务层 (跟 sim 完全一致的数据流) ----
struct DashboardData {
  char title[20];
  int total_balance;
  int today_count;
  int today_net;
  struct {
    char date[8];
    char sign;
    int amount;
    char description[32];
  } recent[5];   // v4.9: 3 → 5 行 (老王要求显示 5 条流水)
  char last_updated[32];
  bool has_error;
  char error_msg[40];
};

DashboardData current_data;
DashboardData last_good;
bool has_last_good = false;

volatile bool should_refresh = false;
unsigned long last_fetch_ms = 0;
unsigned long last_render_ms = 0;
const unsigned long RENDER_INTERVAL_MS = 5000;  // v2.3: 500ms → 5000ms (5s/0.2 FPS, 静态显示足够, 进一步减少撕裂)

// ---- UTF-8 中文检测 ----
bool has_chinese(const char* s) {
  for (int i = 0; s[i]; i++) {
    if ((unsigned char)s[i] >= 0x80) return true;
  }
  return false;
}

// ---- 渲染函数 (v4.2: 全 U8g2 接管 + 数字升 7x13_tr) ----
// ASCII (数字/英文): u8g2 7x13_tr (proportional, 7×13 px, 高匹配 chinese 13)
//   - 字体本身含 baseline 控制, 不需 setTextSize
//   - y 参数是 baseline (字符底部), 跟 chinese3 完全一致 (无需偏移)
//   - 字符高 13 跟 chinese3 一致, 视觉上"数字跟中文同高"
void draw_ascii(VirtualMatrixPanel* d, const char* str, int x, int y, uint16_t color) {
  u8g2.setFont(u8g2_font_7x13_tr);
  u8g2.setFontMode(1);              // 透明背景
  u8g2.setForegroundColor(color);   // RGB565
  u8g2.setCursor(x, y);
  u8g2.print(str);
}

// 中文 (wqy12_t_gb2312b, 5653 字, 12×13 px, GB2312 一级字库 90% 覆盖)
void draw_cn(VirtualMatrixPanel* d, const char* str, int x, int y, uint16_t color) {
  u8g2.setFont(u8g2_font_wqy12_t_gb2312b);
  u8g2.setFontMode(1);              // 透明背景
  u8g2.setForegroundColor(color);   // RGB565
  u8g2.setCursor(x, y);
  u8g2.print(str);
}

// 混排 (一行数字 + 中文, baseline 完美对齐)
//   - v4.2: 数字 7x13_tr 字符高 13, chinese3 字符高 13 → baseline 完全一致, 无偏移
//   - 数字 7 px 宽, chinese 12 px 宽 → 数字视觉上是中文 58% 宽
//   - 视觉: 数字跟中文同高, 数字底部完全对齐 chinese 底部
void draw_mixed(VirtualMatrixPanel* d, const char* ascii_part, const char* cn_part,
                int x, int y_cn, uint16_t color) {
  // 1. 画 ASCII 部分 (数字), baseline = y_cn (跟中文同)
  draw_ascii(d, ascii_part, x, y_cn, color);
  // 2. 计算 ASCII 宽度, 中文起点 = x + 宽 + 2 间隔
  int ascii_w = u8g2.getUTF8Width(ascii_part);
  draw_cn(d, cn_part, x + ascii_w + 2, y_cn, color);
}

// v5.1: 符号→颜色 (全彩 RGB)
//   + → 绿 / - → 红 / 0 → 琥珀 (中性)
uint16_t sign_color(char sign, int amount) {
  if (amount == 0) return COLOR_AMBER;
  return (sign == '-') ? COLOR_RED : COLOR_GREEN;
}

void render_frame() {
  // v4.8: 智能渲染 - 数据没变就跳过整个 render, 屏保持上 1 帧 (静默不闪)
  //   DashboardData 结构 ~100 bytes, memcmp 比较 < 1μs
  //   fetch_dashboard() 每 5s 跑 1 次, 数据没变就 return, 省 50ms 重画时间
  static DashboardData last_rendered;
  static bool first_render = true;

  if (!first_render && memcmp(&current_data, &last_rendered, sizeof(DashboardData)) == 0) {
    return;  // 数据没变, 静默
  }
  first_render = false;
  last_rendered = current_data;

  virtualDisp->fillScreen(COLOR_BLACK);

  // 错误状态
  if (current_data.has_error || !has_last_good) {
    DashboardData* d = has_last_good ? &last_good : &current_data;
    // v4.2 错误状态: 用 7x13_tr 字体 (跟正常态一致), y 是 baseline
    draw_ascii(virtualDisp, d->title, PAD_X, TITLE_Y + 10, COLOR_AMBER);  // TITLE=3 + 字符高 13/2 = 10 (顶部贴 0)
    if (current_data.has_error) {
      draw_ascii(virtualDisp, current_data.error_msg, PAD_X, ROW_2_Y, COLOR_RED_ERR);
    } else {
      draw_ascii(virtualDisp, "WAITING", PAD_X, ROW_2_Y, COLOR_AMBER_DIM);
    }
    draw_ascii(virtualDisp, "T-- ALL:-", PAD_X, FOOTER_Y, COLOR_AMBER);
    return;
  }

  // === 1. 标题 (ASCII, 7x13_tr, baseline y = TITLE+10) ===
  draw_ascii(virtualDisp, current_data.title, PAD_X, TITLE_Y + 10, COLOR_AMBER);

  // === 2. 分隔线 ===
  virtualDisp->drawFastHLine(0, DIVIDER_1_Y, PANEL_RES_X, COLOR_AMBER);
  virtualDisp->drawFastHLine(0, DIVIDER_2_Y, PANEL_RES_X, COLOR_AMBER);

  // === 3. 3 行流水 (v4.0: 去日期 + 数字中文 baseline 对齐) ===
  // 行宽分配: ASCII "+5" 2 字 × 6px = 12px + 2px 间隔 = 14px
  //          中文 wqy12 7 字 × 12px = 84px
  //          总 14 + 84 = 98 px → 装得下 96 屏 (留 PAD_X=4 右边切掉 2px, OK)
  int row_y[5] = { ROW_1_Y, ROW_2_Y, ROW_3_Y, ROW_4_Y, ROW_5_Y };
  for (int i = 0; i < 5; i++) {
    if (strlen(current_data.recent[i].description) > 0) {
      // 左: 金额 (无日期), ASCII 2-3 字符
      char buf[8];
      snprintf(buf, sizeof(buf), "%c%d",
               current_data.recent[i].sign,
               current_data.recent[i].amount);

      // 右: description (v4.7 恢复正常逻辑: 按 "|" 切 + 用 server 真实数据)
      const char* desc = current_data.recent[i].description;
      char desc_trim[24];
      if (has_chinese(desc)) {
        // v4.5 截断逻辑 (按 "|" 分隔符切, 只留前半段)
        //   例: "口算题 | 今天做了20道题" → "口算题 " (3 字)
        //   例: "跳绳 | 跳了100个" → "跳绳 " (2 字)
        //   例: "看动画片 | 超时30分钟" → "看动画片 " (4 字)
        //   后续可以按空格再 split 拿 description 的核心动作
        //   如果没 "|" 就 fallback 到 6 字 (skip ASCII)
        const char* pipe = strchr(desc, '|');
        int head_bytes;
        if (pipe != NULL) {
          head_bytes = pipe - desc;
          // 去掉尾部空格
          while (head_bytes > 0 && desc[head_bytes - 1] == ' ') head_bytes--;
        } else {
          // 没分隔符, 切 6 中文字 (skip ASCII)
          int bc = 0, cc = 0;
          for (int j = 0; desc[j] && cc < 6; j++) {
            if ((unsigned char)desc[j] >= 0x80) {
              bc += 3;
              j += 2;
              cc++;
            }
          }
          head_bytes = bc;
        }
        // 复制 head_bytes 个字节到 desc_trim
        if (head_bytes > (int)sizeof(desc_trim) - 1) head_bytes = sizeof(desc_trim) - 1;
        memcpy(desc_trim, desc, head_bytes);
        desc_trim[head_bytes] = '\0';
      } else {
        // ASCII: 截 10 字
        strncpy(desc_trim, desc, 10);
        desc_trim[10] = '\0';
      }

      // 画混排 (数字 + 中文), baseline 统一对齐
      // v5.0: 数字部分按 sign 选颜色 (+ 亮 / - 暗), 中文 description 保持琥珀亮 (突出动作)
      uint16_t color = sign_color(current_data.recent[i].sign, current_data.recent[i].amount);
      draw_mixed(virtualDisp, buf, desc_trim, PAD_X, row_y[i], color);

    } else {
      // 空行占位
      draw_ascii(virtualDisp, "-", PAD_X, row_y[i], COLOR_AMBER_DIM);
    }
  }

  // === 4. 底栏 (v5.3: "今 +10 ... 总 100" 缩中文 + 14px 间隙 + 3 字符宽稳定) ===
  //   拆 4 段渲染: 今(中文) + 数字(按 sign 颜色) + [14 px 间隙] + 总(中文) + 数字(琥珀)
  //   中文 wqy12 12 px/字, 数字 7x13 7 px/字 (proportional, "1" 更窄 ~5 px)
  //   today_buf 固定 3 字符宽 (%+3d): 0→" +0", 10→"+10", 99→"+99" (100+ 溢出但罕见)
  //   total_buf 固定 3 字符宽 (%3d):  0→"  0", 77→" 77", 100→"100"
  //   最坏总宽 (today=+99, balance=100): 12 + 1 + 21 + 16 + 12 + 1 + 19 = 82 px ≤ 92 px 可用 ✅
  {
    int x = PAD_X;
    // "今" (v5.3: 缩 "今日" → "今", 省 12 px)
    draw_cn(virtualDisp, "今", x, FOOTER_Y, COLOR_AMBER);
    x += u8g2.getUTF8Width("今") + 1;  // 12 + 1 = 13 px

    // 今日净增 (按 sign 颜色, 0 琥珀中性)
      char today_buf[8];
      snprintf(today_buf, sizeof(today_buf), "%+3d", current_data.today_net);  // v5.3: %+d → %+3d (固定 3 字符宽)
      uint16_t today_color = (current_data.today_net > 0) ? COLOR_GREEN
                             : (current_data.today_net < 0) ? COLOR_RED
                             : COLOR_AMBER;
      draw_ascii(virtualDisp, today_buf, x, FOOTER_Y, today_color);
      x += u8g2.getUTF8Width(today_buf) + 2 + 2*7;  // v5.3: +2 → +2+14 (加 2 数字位 14 px 间隙)

      // "总" (v5.3: 缩 "总分" → "总", 省 12 px)
      draw_cn(virtualDisp, "总", x, FOOTER_Y, COLOR_AMBER);
      x += u8g2.getUTF8Width("总") + 1;  // 12 + 1 = 13 px

      // 总分 (琥珀, 跟其他余额一致)
      char total_buf[8];
      snprintf(total_buf, sizeof(total_buf), "%3d", current_data.total_balance);  // v5.3: %d → %3d (固定 3 字符宽)
      draw_ascii(virtualDisp, total_buf, x, FOOTER_Y, COLOR_AMBER);
  }
}  // 闭合 render_frame()

// ---- HTTP 拉取 (主) ----
bool fetch_dashboard() {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  String url = String("http://") + SERVER_HOST + ":" + SERVER_PORT + "/api/dashboard";
  http.begin(url);
  http.setTimeout(5000);
  int http_code = http.GET();

  if (http_code != 200) {
    Serial.printf("[fetch] HTTP %d, 失败\n", http_code);
    http.end();
    return false;
  }

  String body = http.getString();
  http.end();

  // ArduinoJson 7.x 兼容: StaticJsonDocument 仍能用, 也可用 JsonDocument
  StaticJsonDocument<1024> doc;
  DeserializationError err = deserializeJson(doc, body);
  if (err) {
    Serial.printf("[fetch] JSON parse 失败: %s\n", err.c_str());
    return false;
  }

  DashboardData d;
  memset(&d, 0, sizeof(d));
  strncpy(d.title, doc["title"] | "KID POINTS", sizeof(d.title) - 1);

  if (doc["_error"].is<const char*>()) {
    d.has_error = true;
    strncpy(d.error_msg, doc["_error"], sizeof(d.error_msg) - 1);
  } else {
    d.has_error = false;
  }

  d.total_balance = (int)(doc["total_balance"] | -1.0);
  d.today_count   = doc["today_count"]   | 0;
  d.today_net     = doc["today_net"]     | 0;
  strncpy(d.last_updated, doc["last_updated"] | "", sizeof(d.last_updated) - 1);

  JsonArray recent = doc["recent"].as<JsonArray>();
  for (size_t i = 0; i < 5 && i < recent.size(); i++) {
    strncpy(d.recent[i].date, recent[i]["date"] | "", sizeof(d.recent[i].date) - 1);
    const char* sign = recent[i]["type"] | "+";
    d.recent[i].sign = (sign[0] == '-' ? '-' : '+');
    d.recent[i].amount = abs(recent[i]["amount"] | 0);
    strncpy(d.recent[i].description, recent[i]["description"] | "", sizeof(d.recent[i].description) - 1);
  }

// v4.3: 删 debug mode (v4.2 那段强制覆盖 description 已删)
  //       让 server 真实 description 走截断逻辑 (跳 ASCII, 切 6 中文字)

  current_data = d;
  last_good = d;
  has_last_good = true;
  Serial.printf("[fetch] OK: balance=%d, today_count=%d, today_net=%d, recent=%d\n",
                d.total_balance, d.today_count, d.today_net, recent.size());
  return true;
}

// ---- Wi-Fi 自动重连 ----
void ensure_wifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("[wifi] 连 %s...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 30) {
    delay(100);
    retry++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[wifi] 连上, IP=%s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("[wifi] 3s 内未连上, 后台继续重试");
  }
}

// ---- HTTP 拉取 (主) ----
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("=== desktop-dashboard M1.4 v4.8 ===");
  Serial.println("v4.8: 智能渲染 (数据没变不重画)");

  // 0. WiFi 先连(仿 wifitest, I2S 之前)
  Serial.println("[v2.7] WiFi init...");
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.disconnect();
  delay(100);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  for (int i = 0; i < 50; i++) {
    delay(200);
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("[v2.7] WiFi 连上, IP=%s\n", WiFi.localIP().toString().c_str());
      break;
    }
  }
  if (WiFi.status() != WL_CONNECTED) Serial.println("[v2.7] WiFi 10s timeout, 继续 I2S...");

  // 1. HUB75 (v2.0.7 店家伙 + 100% 复刻 HUB75E.txt L25-40)
  // 注意: mxconfig 必须在函数内 (库不允许全局 struct 字段修改)
  HUB75_I2S_CFG mxconfig(PANEL_RES_X, PANEL_RES_Y, PANEL_CHAIN);
  mxconfig.gpio.e = 16;  // 店家伙默认 E=16
  // v2.7: 关 double buffer, 给 WiFi 留更多 RAM
  // mxconfig.double_buff = true;
  dma_display = new MatrixPanel_I2S_DMA(mxconfig);
  if (not dma_display->begin()) {
    Serial.println("KABOOM! I2S allocation failed");
    while (true) delay(1000);
  }
  dma_display->setBrightness8(BRIGHTNESS);  // v2.0.7 API
  dma_display->fillScreen(COLOR_BLACK);

  // 2. VirtualMatrixPanel (店家 HUB75E.txt L40: SERPENT=false TOPDOWN=false)
  virtualDisp = new VirtualMatrixPanel(
    (*dma_display), NUM_ROWS, NUM_COLS,
    PANEL_RES_X, PANEL_RES_Y, SERPENT, TOPDOWN
  );
  virtualDisp->fillScreen(COLOR_BLACK);

  // 3. U8g2 中文桥接 (绑到 virtualDisp, 2 块链 virtual)
  u8g2.begin(*virtualDisp);

  // v4.8: boot 文本用 U8g2 7x13_tr
  draw_ascii(virtualDisp, "BOOT v4.8", PAD_X, (PANEL_RES_Y / 2) + 6, COLOR_AMBER);

  // v4.2: 不开 WebServer/OTA (v2.7 决策: 36KB RAM + I2S DMA 共存)
  // 6. 启动时拉 1 次
  delay(500);
  fetch_dashboard();
}

void loop() {
  // 1. Wi-Fi 看护
  static unsigned long last_wifi_check = 0;
  if (WiFi.status() != WL_CONNECTED && last_wifi_check == 0) {
    Serial.println("[loop] WiFi 断连!");
  }

  // 2. 30s 拉 or WS 触发立即拉
  if (should_refresh || (millis() - last_fetch_ms > FETCH_INTERVAL_MS)) {
    should_refresh = false;
    last_fetch_ms = millis();
    fetch_dashboard();
  }

  // 4. 渲染 (v2.3: 5s/帧)
  if (millis() - last_render_ms > RENDER_INTERVAL_MS) {
    last_render_ms = millis();
    render_frame();
  }
}
