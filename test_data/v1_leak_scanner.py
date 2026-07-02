"""快速扫描 120 条 input.log,识别 V1 漏扣高风险消息
- 找同时含 加X分/加X积分 + 扣X分/减X分 的消息
- 数条数、估算 V1 漏扣金额
- 给出 V2 验证建议列表(挑覆盖各种场景的 N 条)
"""
import re
import json
from collections import defaultdict

INPUT = "/home/wang/桌面/龙虾工作区/StuAgent/New project/kids-points-runtime/test_data/replay_messages.jsonl"
V1_BALANCE = "/home/wang/.openclaw/agents/kids-study/workspace/kids-points/balance.json"

# 1. 读 120 条
messages = []
with open(INPUT, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            messages.append(json.loads(line))
print(f"总消息数: {len(messages)}")

# 2. 识别"混合消息"(同时含 加/加 + 扣/减/没/未)
# 收入: 加X分, 加X积分
# 支出: 扣X分, 减X分, 买X, 消费X
add_pattern = re.compile(r"加\s*(\d+(?:\.\d+)?)\s*(?:分|积分)")
sub_pattern = re.compile(r"(?:扣|减|没|未|忘|没有|不写|不想)\s*.*?(\d+(?:\.\d+)?)\s*(?:分|积分)?|买[^,，。]*?(\d+(?:\.\d+)?)\s*分")
# 更宽松:只要 text 同时出现 "加N分" 和 "扣N分" 或 "没/未/忘" + 分
mixed_messages = []
simple_messages = []
for msg in messages:
    text = msg["text"]
    has_add = bool(re.search(r"加\s*\d", text)) or "加" in text and "分" in text
    has_sub = bool(re.search(r"(?:扣|减)\s*\d", text))
    has_omit = bool(re.search(r"(?:没|未|忘|没有|不写|不想)[^,，。]*?(?:\d|分)", text))
    if (has_add and (has_sub or has_omit)) or (has_sub and has_add):
        mixed_messages.append(msg)
    else:
        simple_messages.append(msg)

not_sub = r'(?:扣|减|没|未|忘|消费|买|花)\s*\d'  # noqa
not_add = r'加\s*\d'  # noqa
print(f"\n=== 风险分类 ===")
print(f"  纯 income (只有加X分): {sum(1 for m in messages if not re.search(not_sub, m['text']))}")
print(f"  纯 expense (只有扣X分/消费): {sum(1 for m in messages if re.search(not_sub, m['text']) and not re.search(not_add, m['text']))}")
print(f"  混合消息 (V1 漏扣高风险): {len(mixed_messages)}")
print(f"  其他: {len(simple_messages)}")

# 3. 估算 V1 漏扣金额
# V1 解析方式猜测:对每条消息,所有"加N"累加,所有"扣N"累加,最后合并为单笔
# V1 bug 表现:只输出 income(包含 income 笔数 sum),丢 expense
# 所以 V1 漏扣 = 消息里所有"扣X分/没X分" 的 X 总和
print(f"\n=== V1 漏扣估算(粗) ===")
total_leak = 0
leak_per_msg = []
for msg in mixed_messages:
    text = msg["text"]
    # 提取所有"扣X分"
    sub_matches = re.findall(r"扣\s*(\d+(?:\.\d+)?)\s*分", text)
    # 提取所有"没/未/忘 + 分"形式
    omit_matches = re.findall(r"(?:没|未|忘|不写|不想)\s*[^,，。]*?(\d+)\s*分", text)
    # 提取"买X花了Y分"形式
    buy_matches = re.findall(r"(?:买|消费|花)[^,，。]*?(\d+)\s*分", text)
    leak = sum(float(x) for x in sub_matches + omit_matches + buy_matches)
    total_leak += leak
    leak_per_msg.append((msg["date"], msg["text"], leak))

print(f"  混合消息数: {len(mixed_messages)}")
print(f"  估算 V1 漏扣总额: {total_leak:.1f} 分")
print(f"  估算 V1 漏扣均值: {total_leak/max(1,len(mixed_messages)):.2f} 分/条")

# 4. 按日期聚合
leak_by_date = defaultdict(float)
count_by_date = defaultdict(int)
for date, text, leak in leak_per_msg:
    leak_by_date[date] += leak
    count_by_date[date] += 1
print(f"\n  按日期分布:")
for date in sorted(leak_by_date.keys()):
    if leak_by_date[date] > 0:
        print(f"    {date}: {count_by_date[date]} 条, 漏扣 {leak_by_date[date]:.1f} 分")

# 5. V1 balance.json 当前余额
v1 = json.load(open(V1_BALANCE))
print(f"\n=== V1 当前状态 ===")
print(f"  currentBalance: {v1['currentBalance']}")
print(f"  lastUpdated: {v1['lastUpdated']}")
print(f"  history 条数: {len(v1['history'])}")

# 6. V2 验证建议:挑 6 条覆盖各种场景
print(f"\n=== V2 验证建议(挑 6 条) ===")
# 优先级:大额漏扣 > 不同日期 > 多种句式
sorted_leak = sorted(leak_per_msg, key=lambda x: -x[2])
for date, text, leak in sorted_leak[:6]:
    print(f"  [{date}] leak={leak:.1f}: {text[:80]}")

# 7. 写报告
report = f"""# V1 漏扣高风险扫描报告

**扫描时间**: 2026-06-12 06:50
**输入**: test_data/replay_messages.jsonl ({len(messages)} 条)
**V1 数据源**: ~/.openclaw/agents/kids-study/workspace/kids-points/balance.json

---

## 风险分类

| 类别 | 条数 | 说明 |
|---|---|---|
| 纯 income (只有加X分) | {sum(1 for m in messages if not re.search(not_sub, m['text']))} | V1 解析无误 |
| 纯 expense (只有扣/消费) | {sum(1 for m in messages if re.search(not_sub, m['text']) and not re.search(not_add, m['text']))} | V1 解析无误 |
| **混合消息 (V1 漏扣高风险)** | **{len(mixed_messages)}** | **需 V2 验证** |
| 其他 | {len(simple_messages)} | — |

## V1 漏扣估算

| 指标 | 值 |
|---|---|
| 混合消息数 | {len(mixed_messages)} |
| **估算 V1 漏扣总额** | **{total_leak:.1f} 分** |
| 估算 V1 漏扣均值 | {total_leak/max(1,len(mixed_messages)):.2f} 分/条 |

⚠️ **注意**:这是**最坏情况**估算(假设 V1 对所有混合消息都漏扣 expense)。实际漏扣数会少于这个值(因为 V1 在 5/19 之后某些版本可能已经部分修复)。**准确数字必须 V2 全跑 120 条后才知道**。

## 按日期分布

| 日期 | 混合消息数 | 估算漏扣 |
|---|---|---|
"""
for date in sorted(leak_by_date.keys()):
    if leak_by_date[date] > 0:
        report += f"| {date} | {count_by_date[date]} | {leak_by_date[date]:.1f} 分 |\n"

report += f"""
## V1 当前状态

- currentBalance: {v1['currentBalance']}
- lastUpdated: {v1['lastUpdated']}
- history 条数: {len(v1['history'])}

## V2 验证建议(高优先 6 条)

为快速验证 V2 是否能解掉 V1 漏扣,挑以下 6 条给 V2 跑(覆盖大额/不同日期/多种句式):
"""
for date, text, leak in sorted_leak[:6]:
    report += f"\n- [{date}] 漏扣 ≈{leak:.1f} 分: {text[:100]}"

report += """

---

## 解法路径

### 选项 A: 立即行动(0 成本)
**老王手动核对 balance.json + 历史日报**,对每条混合消息决定补不补。耗时 1-2 小时。

### 选项 B: V2 全跑 120 条(本 session 自动,推荐)
1. 当前 7:00 T6 wet run 跑 30 条 → 7:10 出 T7 报告(30 条对比)
2. 看 30 条结果,如果 V1 漏扣表现符合预期 → 跑全量 120 条
3. 全量出"补偿建议表"(V1/V2 净金额差,逐条),老王手动确认
4. 累计 LLM 调用:120 × 4s × 4 = 32 分钟

### 选项 C: V2 修补脚本(技术性补)
写一个 `replay_v1_audit.py` 脚本,直接读 V1 balance.json + V2 replay.db,生成"V1 错账审计报告",**不动 V1 数据**,只标记。

---

**推荐**: 选项 B(自然衔接 T6/T7 流程,老王几乎零成本)

"""
with open("/home/wang/桌面/龙虾工作区/StuAgent/New project/kids-points-runtime/test_data/v1_leak_scan.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"\n✓ 报告写到 test_data/v1_leak_scan.md")
