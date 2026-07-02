#!/usr/bin/env python3
"""分组执行 E2E 测试"""
import sys, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

import runtime.pipeline as pl
from runtime.db import init_db

def test_group(name, test_cases):
    conn = init_db(":memory:")
    print(f"\n=== {name} ===")
    start = time.time()
    for msg_id, text in test_cases:
        try:
            r = pl.process_message(conn, msg_id, text)
            elapsed = time.time() - start
            if r["status"] == "ok":
                row = conn.execute("SELECT type, amount, description FROM transactions WHERE id=?", (msg_id,)).fetchone()
                if row:
                    print(f"  {msg_id}[{elapsed:.1f}s]: {r['status']} -> {row['type']} amount={row['amount']} {row['description'][:20]}")
                else:
                    print(f"  {msg_id}[{elapsed:.1f}s]: {r['status']} -> {r['reply'][:60]}")
            else:
                print(f"  {msg_id}[{elapsed:.1f}s]: {r['status']} -> {r['reply'][:60]}")
        except Exception as e:
            print(f"  {msg_id}: ERROR: {e}")
    print(f"  总耗时: {time.time()-start:.1f}s")
    conn.close()

test_group("加分", [("a-001", "扫地加5分"), ("a-002", "洗碗加2分")])

test_group("扣分", [("b-001", "买零食扣2分"), ("b-002", "冰激凌扣4分")])

test_group("多笔", [("c-001", "口算加1分，买冰激凌扣4分")])

test_group("查询", [("d-001", "扫地加5分"), ("d-002", "买玩具扣2分"), ("d-003", "查余额"), ("d-004", "今天统计")])

test_group("调账", [("e-001", "口算加1分"), ("e-002", "调账 口算加到2分"), ("e-003", "确认")])

test_group("异常", [("f-001", "扣-1分"), ("f-002", "加9999分"), ("f-003", ""), ("f-004", "的风格的风格是大幅"), ("f-005", "扫地加5分")])

test_group("时序连续", [("g-001", "扫地加3分"), ("g-002", "洗碗加2分"), ("g-003", "跳绳加5分"), ("g-004", "买饮料扣1分")])
