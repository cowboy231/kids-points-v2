#!/usr/bin/env python3
"""分组执行 E2E 测试"""
import sys, json, traceback, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3
from runtime.db import init_db
import pip...[truncated]