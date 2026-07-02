#!/usr/bin/env python3
"""追踪 pipeline 中 classify 的全链路"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# 模拟 pipeline 的导入和调用
import runtime.pipeline
from llm_config import call_llm

CLASSIFY_PROMPT = pipeline.CLASSIFY_PROMPT

# 测试各种消息
test_messages = [
    "扫地加5分",
    "买零食扣2分",
    "查余额",
    "调账：昨天口算应该是2分",
    "今天统计",
]

for msg in test_messages:
    print("=" * 50)
    print(f"消息: {msg}")
    print("-" * 50)
    prompt = CLASSIFY_PROMPT.format(message=msg)
    try:
        resp = call_llm(prompt)
        print(f"LLM 原始回复 ({len(resp)} chars): {resp[:200]}")
        data = json.loads(resp)  # 直接 JSON 解析
        print(f"✅ JSON 解析成功: {json.dumps(data, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ JSON 解析失败: {e}")
        print(f"  原始内容前500: {resp[:500]}")
    print()
