#!/usr/bin/env python3
"""Export 5/12-6/11 原始飞书消息(input.log) -> replay_messages.jsonl"""
import re, json
from collections import Counter
from pathlib import Path

BASE = Path("/home/wang/.openclaw/agents/kids-study/workspace/kids-points")
RUNTIME = Path("/home/wang/桌面/龙虾工作区/StuAgent/New project/kids-points-runtime")
SRC = BASE / "logs/input.log"
DST = RUNTIME / "test_data" / "replay_messages.jsonl"

pattern = re.compile(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] .+? "(.+?)"$')

out = []
with open(SRC) as f:
    for line in f:
        line = line.rstrip()
        m = pattern.match(line)
        if m:
            ts = m.group(1)
            if "2026-05-12" <= ts[:10] <= "2026-06-11":
                out.append({
                    "timestamp": ts,
                    "date": ts[:10],
                    "text": m.group(2),
                })

# 按 timestamp 排序,文本去重(保留最早一次出现)
out.sort(key=lambda x: x["timestamp"])
seen, deduped = set(), []
for o in out:
    if o["text"] not in seen:
        seen.add(o["text"])
        deduped.append(o)

DST.parent.mkdir(parents=True, exist_ok=True)
with open(DST, "w") as f:
    for o in deduped:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")

print(f"原始 {len(out)} 条 -> 去重后 {len(deduped)} 条")
print(f"输出: {DST}")
print(f"\n日期分布(去重后):")
dates = Counter(o["date"] for o in deduped)
for d in sorted(dates):
    print(f"  {d}: {dates[d]} 条")
