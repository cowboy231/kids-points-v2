#!/usr/bin/env python3
"""精确追踪 E-002 的错误路径"""
import sys, json, traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3
from runtime.db import init_db
import runtime.pipeline

conn = init_db(":memory:")

try:
    r = pipeline.process_message(conn, "e-002", "扣-1分")
    print(f"Status: {r}")
except Exception as e:
    traceback.print_exc()
