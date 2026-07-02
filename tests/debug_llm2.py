#!/usr/bin/env python3
"""测试 MiniMax 2.7 是否支持参数关闭 thinking"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# 直接测试 raw API，加 reasoning_effort 参数
import urllib.request

from llm_config import LLM_API_KEY, LLM_API_URL, LLM_MODEL

body = json.dumps({
    "model": LLM_MODEL,
    "messages": [{"role": "user", "content": "扫地加5分。只返回 JSON：{\"intent\": \"record|adjust|query\", \"reasoning\": \"原因\"}"}],
    "stream": False,
}).encode("utf-8")

req = urllib.request.Request(LLM_API_URL, data=body, method="POST")
req.add_header("Authorization", f"Bearer {LLM_API_KEY}")
req.add_header("Content-Type", "application/json")

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    print("完整响应:")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    print("\n提取 content:")
    print(repr(content))
except Exception as e:
    print(f"错误: {e}")
