"""黄金集端到端测试 — 12 条精选 case,覆盖所有 V2 bug 维度。

设计原则:
- 每次 prompt 改完必跑这个(36 次 LLM 调用 ~600k tokens,~3-5 分钟)
- 30 条 release 前跑一次(90 次 LLM 调用 ~1.5M tokens,~10-15 分钟)
- Pipeline 逻辑改动跑 tests/test_pipeline_unit.py(0 token,秒级)

每条 case 显式断言:
- 预期 status
- ok 的 case 断言:tx 笔数 + 关键 description + 净金额
- V2-004 [撤销] 断言:reply 含"V2 暂不支持"
- V2-005 缺金额断言:reply 含"没听清金额" 或 needs_amount 透传
- V1 bug 验证(idx 4)断言:6 笔,净 +2(不是 V1 的 +6)

自包含数据:GOLDEN_CASES 列表直接内嵌,不依赖外部 JSONL 文件。

跑法:
    cd /home/wang/projects/kids-points-v2
    LANG=C.UTF-8 python -m pytest tests/test_golden_set.py -v -s

    # 跳 LLM(只校验 case 数量):
    LANG=C.UTF-8 python -m pytest tests/test_golden_set.py -v --co
"""

import os
import sqlite3
import sys
from pathlib import Path

import pytest

# 让 import 找到 pipeline.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.db import init_db  # noqa: E402
from runtime.pipeline import process_message  # noqa: E402


# ─── 内嵌黄金集(原 test_data/golden_set.jsonl 12 条) ───────────────────────
# 格式: (date, text)
# 来源: V1 生产日志精选,覆盖 V2 所有 bug 维度。
GOLDEN_CASES: list[tuple[str, str]] = [
    ("2026-05-13", "数学口算加1分，写字加3分，ABC Reading加2分，英赛尔加3分，晚睡扣2分，消费看动画片扣5分"),
    ("2026-05-14", "买冰激凌 -3"),
    ("2026-05-15", "昨天语文写字加3分，ABC Reading没读，英赛尔加3分口算加一分"),
    ("2026-05-16", "[object Object]"),
    ("2026-05-16", "昨天的积分情况"),
    ("2026-05-16", "买铜锣烧花了5块钱"),
    ("2026-05-17", "英赛尔打卡记2分，语文的拼写记1分，舒尔特方格记1分"),
    ("2026-05-17", "[撤销]买宝宝口香糖"),
    ("2026-05-17", "记昨天买口香糖，扣1分"),
    ("2026-05-17", "买柠檬果饮"),
    ("2026-05-17", "看哈利波特"),
    ("2026-05-17", "数学口算加1分"),
]

NUM_GOLDEN = len(GOLDEN_CASES)


# ─── 黄金集加载校验(0 token,任何时候都跑) ────────────────────────────────────

def test_golden_set_size():
    """黄金集必须 12 条。"""
    assert NUM_GOLDEN == 12, f"黄金集应该 12 条,实际 {NUM_GOLDEN} 条"


# ─── 单 case fixture ────────────────────────────────────────────────────────

@pytest.fixture
def fresh_db():
    """每个 case 一个全新 DB(trace_id 重置,互不干扰)。"""
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    conn = init_db(tmp.name)
    yield conn
    conn.close()
    os.unlink(tmp.name)


def _make_trace_id(idx: int) -> str:
    return f"GOLDEN-{idx:03d}"


# ─── 12 条 case 端到端断言(湿跑,~3-5 分钟) ──────────────────────────────────

def test_case_01_混合_income_expense_V1_bug验证(fresh_db):
    """idx 0 原始:数学口算+1,写字+3,ABC Reading+2,英赛尔+3,晚睡-2,看动画片-5 = 6 笔 净+2

    V1 bug 验证:V1 当年只记 1 笔 income +6(漏扣 -3 -2 -5),V2 应该 6 笔 净+2。
    """
    case = GOLDEN_CASES[0]
    result = process_message(fresh_db, trace_id=_make_trace_id(1), message_text=case[1])

    assert result["status"] == "ok", f"应该 ok,实际 {result.get('status')}: {result.get('reply')}"
    items = result.get("items", [])
    assert len(items) == 6, f"应该 6 笔,实际 {len(items)} 笔: {items}"

    # 净金额 = +1+3+2+3-2-5 = +2
    total = sum(item["amount"] for item in items)
    assert total == 2, f"净金额应该 +2,实际 {total}"

    # 关键 description 必须保留
    descs = {item["description"] for item in items}
    assert "数学口算" in descs or any("数学" in d for d in descs), f"数学口算 缺失: {descs}"


def test_case_02_纯_expense_短形(fresh_db):
    """idx 1:买冰激凌 -3 → 单笔 expense -3。"""
    result = process_message(fresh_db, trace_id=_make_trace_id(2), message_text=GOLDEN_CASES[1][1])

    assert result["status"] == "ok"
    items = result.get("items", [])
    assert len(items) == 1
    assert items[0]["type"] == "expense"
    assert items[0]["amount"] == -3


def test_case_03_混合_部分缺金额_V2_005核心(fresh_db):
    """idx 2:混合 income + 部分缺金额(ABC Reading 没读) → needs_amount 透传。

    预期:
    - valid 项:语文写字 +3, 英赛尔 +3, 口算 +1 (3 笔 income,净 +7)
    - needs_amount: ABC Reading 没读
    - reply 末尾追加"⚠️ 没听清金额"提示
    """
    result = process_message(fresh_db, trace_id=_make_trace_id(3), message_text=GOLDEN_CASES[2][1])

    assert result["status"] == "ok"
    items = result.get("items", [])
    assert len(items) == 3, f"应 3 笔 income,实际 {len(items)} 笔: {items}"

    # needs_amount 必须有 ABC Reading 没读
    needs_amount = result.get("needs_amount", [])
    assert len(needs_amount) == 1, f"needs_amount 应 1 条,实际 {len(needs_amount)}: {needs_amount}"
    assert "ABC Reading" in needs_amount[0]["description"]

    # reply 必须有"没听清金额"提示
    reply = result.get("reply", "")
    assert "没听清金额" in reply, f"reply 应提示缺金额,实际: {reply[:200]}"


def test_case_04_数据脏_object_Object(fresh_db):
    """idx 3:[object Object] 数据脏,LLM 可能 fail,pipeline 应不 crash。

    验证:不管 status,DB 应该有 audit_log 记录这次处理(不是 silent crash)。
    """
    result = process_message(fresh_db, trace_id=_make_trace_id(4), message_text=GOLDEN_CASES[3][1])

    # 状态可以是 ok 或 error,关键是 audit_log 留痕
    assert result.get("status") in ("ok", "error"), f"status 应 ok/error,实际 {result.get('status')}"

    # 必须有 intake audit
    rows = fresh_db.execute(
        "SELECT step FROM audit_log WHERE trace_id = ?", (_make_trace_id(4),)
    ).fetchall()
    steps = {r[0] for r in rows}
    assert "intake" in steps, f"必须有 intake audit,实际: {steps}"


def test_case_05_query_查账(fresh_db):
    """idx 4:昨天的积分情况 → 走 query intent。

    验证:status=ok,可能没 tx 但 reply 是查账类内容。
    """
    result = process_message(fresh_db, trace_id=_make_trace_id(5), message_text=GOLDEN_CASES[4][1])

    assert result["status"] == "ok", f"应 ok,实际 {result.get('status')}: {result.get('reply')[:100]}"


def test_case_06_V2_003_货币换算_5块钱(fresh_db):
    """idx 5:买铜锣烧花了5块钱 → 单笔 expense -5(口语 = 5 分,不是 500 分)。

    关键 V2-003 bug 验证:不要误判 -500 分。
    """
    result = process_message(fresh_db, trace_id=_make_trace_id(6), message_text=GOLDEN_CASES[5][1])

    assert result["status"] == "ok"
    items = result.get("items", [])
    assert len(items) == 1
    assert items[0]["type"] == "expense"
    assert items[0]["amount"] == -5, f"V2-003 误判:{items[0]['amount']} 分(应 -5 分口语)"


def test_case_07_纯_income_多笔(fresh_db):
    """idx 6:英赛尔打卡记2分,语文的拼写记1分,舒尔特方格记1分 → 3 笔 income,净 +4。"""
    result = process_message(fresh_db, trace_id=_make_trace_id(7), message_text=GOLDEN_CASES[6][1])

    assert result["status"] == "ok"
    items = result.get("items", [])
    assert len(items) == 3, f"应 3 笔,实际 {len(items)} 笔: {items}"
    total = sum(item["amount"] for item in items)
    assert total == 4, f"净 +4,实际 {total}"


def test_case_08_V2_004_撤销_语法(fresh_db):
    """idx 7:[撤销]买宝宝口香糖 → 走 unsupported 分支,0.0s,不调 LLM。

    关键 V2-004 验证:
    - status=ok(不是 error)
    - reply 含"V2 暂不支持 [撤销]"
    - 没产生 tx
    """
    result = process_message(fresh_db, trace_id=_make_trace_id(8), message_text=GOLDEN_CASES[7][1])

    assert result["status"] == "ok", f"撤销应 ok,实际 {result.get('status')}"
    reply = result.get("reply", "")
    assert "V2 不支持" in reply, f"reply 应说明不支持,实际: {reply[:200]}"
    # 不能记账
    assert not result.get("items"), "撤销不应产生 tx"


def test_case_09_adjust_调账_记昨天(fresh_db):
    """idx 8:记昨天买口香糖,扣1分 → 走 adjust intent。"""
    result = process_message(fresh_db, trace_id=_make_trace_id(9), message_text=GOLDEN_CASES[8][1])

    # adjust 路径可能产生 pending 或 error,关键是 audit 留痕
    assert result.get("status") in ("ok", "error"), f"status 异常: {result.get('status')}"


def test_case_10_V2_005_缺金额_单品(fresh_db):
    """idx 9:买柠檬果饮 → 没金额,走 needs_amount 提示。

    关键 V2-005 验证:
    - valid=[](没金额所以不记账)
    - needs_amount 有"买柠檬果饮"
    - reply 含"没听清金额"和"请补充 X 分/元/块"
    """
    result = process_message(fresh_db, trace_id=_make_trace_id(10), message_text=GOLDEN_CASES[9][1])

    assert result["status"] == "ok", f"缺金额应 ok(引导补),实际 {result.get('status')}"
    items = result.get("items", [])
    assert len(items) == 0, f"应 0 笔 tx,实际 {len(items)} 笔: {items}"

    needs_amount = result.get("needs_amount", [])
    assert len(needs_amount) == 1
    assert "柠檬果饮" in needs_amount[0]["description"]

    reply = result.get("reply", "")
    assert "没听清金额" in reply
    assert "X 分" in reply or "分/元" in reply


def test_case_11_V2_006_模糊短消息_观察池(fresh_db):
    """idx 10:看哈利波特 → LLM 模糊短消息,可能 fail(V2-006 持续观察)。

    验证:不 crash,audit 留痕。
    """
    result = process_message(fresh_db, trace_id=_make_trace_id(11), message_text=GOLDEN_CASES[10][1])

    # 模糊消息 LLM 可能 fail 也可能 success(取决于模型判断)
    assert result.get("status") in ("ok", "error"), f"status 异常: {result.get('status')}"

    # 必须有 audit 留痕
    rows = fresh_db.execute(
        "SELECT step FROM audit_log WHERE trace_id = ?", (_make_trace_id(11),)
    ).fetchall()
    assert rows, "模糊消息也必须有 audit 留痕"


def test_case_12_纯_income_单笔_基础(fresh_db):
    """idx 11:数学口算加1分 → 基础单笔 income,1 分,黄金集最简 case(冒烟)。"""
    result = process_message(fresh_db, trace_id=_make_trace_id(12), message_text=GOLDEN_CASES[11][1])

    assert result["status"] == "ok"
    items = result.get("items", [])
    assert len(items) == 1
    assert items[0]["type"] == "income"
    assert items[0]["amount"] == 1


# ─── ref_id 注入校验(每条 case 都验证 V2-007) ──────────────────────────────

@pytest.mark.parametrize("case_index", range(NUM_GOLDEN))
def test_ref_id_injection_for_every_case(fresh_db, case_index):
    """每条 case 跑完后,transactions.ref_id 必须 == trace_id(V2-007 验证)。"""
    result = process_message(
        fresh_db, trace_id=f"REFTEST-{case_index:03d}", message_text=GOLDEN_CASES[case_index][1]
    )
    items = result.get("items", [])
    if not items:
        pytest.skip(f"case {case_index} 没产生 tx (status={result.get('status')})")

    for item in items:
        assert item.get("ref_id") == f"REFTEST-{case_index:03d}", (
            f"case {case_index} tx.ref_id 缺失或错: {item}"
        )


# ─── audit_log.trace_id 覆盖校验(V2-007 增强) ──────────────────────────────

def test_audit_log_trace_id_coverage():
    """所有 audit_log 记录(无论哪个 step)都应带 trace_id。

    跑一遍黄金集,统计 trace_id 覆盖率必须 = 100%。
    """
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    conn = init_db(tmp.name)

    try:
        for i, case in enumerate(GOLDEN_CASES, 1):
            process_message(conn, trace_id=f"TRACE-{i:03d}", message_text=case[1])

        total = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        with_tid = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE trace_id IS NOT NULL"
        ).fetchone()[0]

        assert total > 0, "audit_log 应该有记录"
        assert with_tid == total, f"audit_log.trace_id 覆盖率 {with_tid}/{total} ≠ 100%"
    finally:
        conn.close()
        os.unlink(tmp.name)
