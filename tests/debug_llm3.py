#!/usr/bin/env python3
"""测试 call_llm think 标签过滤"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from llm_config import call_llm

# 测试 1: 分类
print("=" * 40)
print("测试 1: 意图分类")
print("=" * 40)
try:
    resp = call_llm(
        '你是一个积分记账系统的意图分类器。用户消息：扫地加5分。\n'
        '请返回 JSON：{"intent": "record"|"adjust"|"query", "reasoning": "原因"}\n'
        '只返回 JSON，不要其他内容。'
    )
    print(f"原始响应: {resp[:200]}")
    data = json.loads(resp)
    print(f"JSON 解析 OK: {json.dumps(data, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 错误: {e}")

print()

# 测试 2: 解析
print("=" * 40)
print("测试 2: 解析记账")
print("=" * 40)
try:
    resp = call_llm(
        '你是一个积分记账系统的交易解析器。用户消息：口算加1分，买冰激凌扣4分。\n'
        '请返回 JSON 数组：\n'
        '[{"type": "income"|"expense", "amount": 数字, "description": "描述"}]\n'
        '只返回 JSON 数组，不要其他内容。'
    )
    print(f"原始响应: {resp[:200]}")
    data = json.loads(resp)
    print(f"JSON 解析 OK: {json.dumps(data, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 错误: {e}")

print()

# 测试 3: 鼓励语（纯文本，无 JSON）
print("=" * 40)
print("测试 3: 鼓励语（纯文本）")
print("=" * 40)
try:
    resp = call_llm(
        '你是一个温暖的家长助手。当前余额：10分。请给一句简短的鼓励或点评。\n'
        '只返回一句话，不要引号。'
    )
    print(f"响应: {resp[:100]}")
except Exception as e:
    print(f"❌ 错误: {e}")
