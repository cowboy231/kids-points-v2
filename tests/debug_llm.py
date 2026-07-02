#!/usr/bin/env python3
"""单独测试 MiniMax 2.7 的意图分类能力"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from llm_config import call_llm

# 测试分类
test_msg = "扫地加5分"
prompt = """你是一个积分记账系统的意图分类器。分析用户消息，判断意图。

用户消息：""" + test_msg + """

请返回 JSON：
{
    "intent": "record" | "adjust" | "query",
    "reasoning": "简短说明为什么是这个意图"
}

规则：
- record：用户要加分或减分（如"口算加1分""买冰激凌扣4分"）
- adjust：用户要修正之前的记录（如"昨天的口算应该是加2分不是1分"）
- query：用户在查账（如"现在多少分""本周加了多少""口算一共加了多少"）

只返回 JSON，不要其他内容。"""

print("=" * 50)
print("测试分类 prompt:")
print("=" * 50)
print(prompt[:300] + "...")
print()

try:
    resp = call_llm(prompt)
    print("=" * 50)
    print("LLM 原始响应:")
    print("=" * 50)
    print(repr(resp))
    print()
    data = json.loads(resp.strip())
    print("JSON 解析 OK:", json.dumps(data, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
