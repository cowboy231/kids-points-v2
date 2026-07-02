"""Pipeline 逻辑分支单测 — 0 LLM token,秒级,改 pipeline 时必跑。

覆盖:
- validate_record_items 各种边界
- _handle_record needs_amount 分支
- _handle_record 全部缺金额分支
- _handle_record V2-004 撤销快分支
- db 事务原子性(insert_transactions_batch)
- audit_log.trace_id 全覆盖
- transactions.ref_id 全覆盖

跑法:
    cd /home/wang/桌面/龙虾工作区/StuAgent/New project/kids-points-runtime
    LANG=C.UTF-8 python -m pytest tests/test_pipeline_unit.py -v
"""

import inspect
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.db import (  # noqa: E402
    init_db,
    insert_transactions_batch,
    get_current_balance,
    is_message_processed,
    mark_message_processed,
    log_audit,
    acquire_processing_lock,
    release_processing_lock,
    LockStatus,
)
from runtime.pipeline import (  # noqa: E402
    validate_record_items,
    ValidationError,
    process_message,
)


# ─── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def fresh_db():
    """每个测试一个全新 DB。"""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    conn = init_db(tmp.name)
    yield conn
    conn.close()
    os.unlink(tmp.name)


def _mock_llm(*responses):
    """构造 mock LLM:每次调用返回列表中下一个 response。"""
    it = iter(responses)

    def fn(prompt):
        return next(it)

    return fn


# ─── validate_record_items 边界 ─────────────────────────────────────────────

class TestValidateRecordItems:
    """validate_record_items 的所有边界情况,0 LLM token。"""

    def test_正常多笔_ref_id_注入(self):
        result = validate_record_items([
            {"type": "income", "amount": 2, "description": "口算"},
            {"type": "expense", "amount": 4, "description": "买冰激凌"},
        ], trace_id="T-001")
        assert result["valid"] == [
            {"type": "income", "amount": 2, "description": "口算", "ref_id": "T-001"},
            {"type": "expense", "amount": -4, "description": "买冰激凌", "ref_id": "T-001"},
        ]
        assert result["needs_amount"] == []

    def test_部分缺金额_分桶(self):
        result = validate_record_items([
            {"type": "income", "amount": 1, "description": "口算"},
            {"type": "expense", "amount": None, "description": "买冰激凌"},
        ], trace_id="T-002")
        assert len(result["valid"]) == 1
        assert len(result["needs_amount"]) == 1
        assert result["needs_amount"][0]["description"] == "买冰激凌"

    def test_全部缺金额_valid_空(self):
        result = validate_record_items([
            {"type": "expense", "amount": None, "description": "买冰激凌"},
            {"type": "expense", "amount": None, "description": "买薯片"},
        ])
        assert result["valid"] == []
        assert len(result["needs_amount"]) == 2

    def test_trace_id_为空时_ref_id_兼容(self):
        result = validate_record_items([
            {"type": "income", "amount": 1, "description": "口算"},
        ])
        assert result["valid"][0]["ref_id"] is None

    def test_包装_dict(self):
        result = validate_record_items(
            {"items": [{"type": "income", "amount": 5, "description": "跳绳"}]},
            trace_id="T-004"
        )
        assert result["valid"][0]["ref_id"] == "T-004"

    def test_裸数组_str(self):
        result = validate_record_items(
            '[{"type": "income", "amount": 3, "description": "读英语"}]',
            trace_id="T-005"
        )
        assert result["valid"][0]["ref_id"] == "T-005"

    def test_负数_仍抛错_未回归(self):
        with pytest.raises(ValidationError, match="必须为正数"):
            validate_record_items([{"type": "income", "amount": -5, "description": "测试"}])

    def test_缺_type_仍抛错_未回归(self):
        with pytest.raises(ValidationError, match="type 无效"):
            validate_record_items([{"amount": 5, "description": "测试"}])

    def test_金额过大_仍抛错(self):
        with pytest.raises(ValidationError, match="金额过大"):
            validate_record_items([{"type": "income", "amount": 20000, "description": "测试"}])

    def test_空_items_抛错(self):
        with pytest.raises(ValidationError, match="未解析出任何记账条目"):
            validate_record_items([])

    def test_类型错误_amount(self):
        with pytest.raises(ValidationError, match="金额类型错误"):
            validate_record_items([{"type": "income", "amount": "5", "description": "测试"}])

    # ─── V2-decimal (2026-06-16): 小数积分支持 ────────────────────────────

    def test_小数_income_入账_两位小数(self):
        result = validate_record_items([
            {"type": "income", "amount": 0.5, "description": "跳绳半次"},
        ])
        assert len(result["valid"]) == 1
        assert result["valid"][0]["amount"] == 0.5  # 保留 float, 入账不转 int
        assert result["needs_amount"] == []

    def test_小数_expense_入账_保留负数(self):
        result = validate_record_items([
            {"type": "expense", "amount": 1.5, "description": "半份零食"},
        ])
        assert len(result["valid"]) == 1
        assert result["valid"][0]["amount"] == -1.5

    def test_三位小数_rounded_to_两位(self):
        """0.123 入账, round 到两位 0.12 (V2-decimal 业务规则: 保留两位)"""
        result = validate_record_items([
            {"type": "income", "amount": 0.123, "description": "跳绳"},
        ])
        assert result["valid"][0]["amount"] == 0.12

    def test_浮点误差自动修正(self):
        """0.1 + 0.2 = 0.30000000000000004, round 后应等于 0.3"""
        result = validate_record_items([
            {"type": "income", "amount": 0.1 + 0.2, "description": "口算"},
        ])
        assert result["valid"][0]["amount"] == 0.3

    def test_整数仍可用_未回归(self):
        result = validate_record_items([
            {"type": "income", "amount": 5, "description": "口算"},
            {"type": "expense", "amount": 2, "description": "零食"},
        ])
        assert result["valid"][0]["amount"] == 5
        assert result["valid"][1]["amount"] == -2

    def test_小数_9999_99_上限不报错(self):
        """9999.99 是新上限, 应入账"""
        result = validate_record_items([
            {"type": "income", "amount": 9999.99, "description": "测试上限"},
        ])
        assert result["valid"][0]["amount"] == 9999.99

    def test_小数_10000_0_仍抛错(self):
        """10000.0 超过新上限 9999.99, 仍抛错"""
        with pytest.raises(ValidationError, match="金额过大"):
            validate_record_items([{"type": "income", "amount": 10000.0, "description": "测试"}])

    def test_0_1_仍抛错_未回归(self):
        """amount <= 0 仍抛错 (不能是 0 分也不能是负)"""
        with pytest.raises(ValidationError, match="必须为正数"):
            validate_record_items([{"type": "income", "amount": 0, "description": "测试"}])
        with pytest.raises(ValidationError, match="必须为正数"):
            validate_record_items([{"type": "income", "amount": -0.5, "description": "测试"}])


# ─── V2-decimal: cents_to_display 格式化 ──────────────────────────

class TestCentsToDisplay:
    """V2-decimal (2026-06-16): 显示函数支持两位小数。"""

    def test_整数不带点(self):
        from runtime.db import cents_to_display
        assert cents_to_display(6) == "6"
        assert cents_to_display(6.0) == "6"
        assert cents_to_display(-10) == "-10"
        assert cents_to_display(0) == "0"

    def test_一位小数保留(self):
        from runtime.db import cents_to_display
        assert cents_to_display(0.5) == "0.5"
        assert cents_to_display(6.5) == "6.5"
        assert cents_to_display(-1.5) == "-1.5"

    def test_两位小数保留(self):
        from runtime.db import cents_to_display
        assert cents_to_display(10.25) == "10.25"
        assert cents_to_display(9999.99) == "9999.99"

    def test_尾随_0_去除(self):
        """10.10 → "10.1" (业务上 .10 等价 .1)"""
        from runtime.db import cents_to_display
        assert cents_to_display(10.10) == "10.1"
        assert cents_to_display(0.50) == "0.5"

    def test_负零归零(self):
        from runtime.db import cents_to_display
        assert cents_to_display(-0.0) == "0"
        assert cents_to_display(-0.001) == "0"

    def test_浮点误差自动修正(self):
        """0.1 + 0.2 = 0.30000000000000004 → "0.3" """
        from runtime.db import cents_to_display
        assert cents_to_display(0.1 + 0.2) == "0.3"

    def test_esp_整数兼容(self):
        """ESP32 按整数解析 balance_display 的场景:
        - 整数余额 (6) → "6" (可直接 atoi)
        - 小数余额 (6.5) → "6.5" (ESP 需要先判 ".")
        """
        from runtime.db import cents_to_display
        # 老 V2 路径都是整数, 完全兼容
        assert cents_to_display(6.0).isdigit()
        assert cents_to_display(100.0).isdigit()


# ─── process_message: V2-004 [撤销] 快分支(0 LLM) ──────────────────────────

class TestUndoShortCircuit:
    """[撤销] / 调账 关键词检测走 unsupported 分支,不调 LLM,0 token。
    V2-008/009 合并后:撤销/撤回/取消/作废/调账 关键词都触发。"""

    def test_撤销_不调_LLM_0秒响应(self, fresh_db):
        llm = _mock_llm()  # 没人调用,会用尽抛 StopIteration
        result = process_message(
            fresh_db, trace_id="UNDO-001",
            message_text="[撤销]买宝宝口香糖",
            llm_call=llm,
        )
        assert result["status"] == "ok"
        assert "不支持" in result["reply"] and ("撤销" in result["reply"] or "调账" in result["reply"])
        assert not result.get("items"), "撤销不应产生 tx"

    def test_撤销_audit_留痕_unsupported_intent(self, fresh_db):
        process_message(
            fresh_db, trace_id="UNDO-002",
            message_text="[撤销]扣 10 分",
        )
        rows = fresh_db.execute(
            "SELECT step FROM audit_log WHERE trace_id=?", ("UNDO-002",)
        ).fetchall()
        steps = {r[0] for r in rows}
        assert "unsupported_intent" in steps, f"应有 unsupported_intent 留痕: {steps}"

    def test_撤销_不调_LLM_能验证(self, fresh_db):
        """如果撤销调了 LLM,mock 会抛 StopIteration。"""
        call_count = [0]

        def llm_fn(prompt):
            call_count[0] += 1
            return "{}"

        process_message(
            fresh_db, trace_id="UNDO-003",
            message_text="[撤销]测试",
            llm_call=llm_fn,
        )
        assert call_count[0] == 0, f"撤销不应调 LLM,实际调了 {call_count[0]} 次"


# ─── process_message: V2-016 修正/补录/补打/更正 fast path(0 LLM) ──────────
# 根因 (2026-06-14 Run 4 REPLAY-20260614-038):
#   "昨天ABC Reading +2分（修正）" → LLM classify 走 adjust/查账 → 查不到 → error
# 修复 (2026-06-14 00:30 方案 A 拍板): 跟 V2-008/009 同款, 关键词命中 → 引导重发, 不调 LLM
# 区别 V2-004: "修正" 业务合法, 不拒, 引导按 income/expense 重发

class TestV2_016Shortcut:
    """V2-016 修正/补录/补打/更正 关键词检测走 fast path, 不调 LLM, 0 token。"""

    def test_修正_不调_LLM_0秒响应(self, fresh_db):
        """Run 4 唯一 error 原文, 修后必须走 fast path。"""
        call_count = [0]

        def llm_fn(prompt):
            call_count[0] += 1
            return "{}"

        result = process_message(
            fresh_db, trace_id="V2-016-001",
            message_text="昨天ABC Reading +2分（修正）",
            llm_call=llm_fn,
        )
        assert result["status"] == "ok"
        assert "修正" in result["reply"], f"应提示「修正」关键字: {result['reply'][:200]}"
        assert "income/expense" in result["reply"] or "加" in result["reply"]
        assert call_count[0] == 0, f"修正不应调 LLM, 实际调了 {call_count[0]} 次"

    def test_补录_不调_LLM(self, fresh_db):
        """补录关键词, 应走 fast path。"""
        llm = _mock_llm()
        result = process_message(
            fresh_db, trace_id="V2-016-002",
            message_text="补录 昨天数学口算+1",
            llm_call=llm,
        )
        assert result["status"] == "ok"
        assert "补录" in result["reply"]

    def test_补打_不调_LLM(self, fresh_db):
        """补打关键词 (同款修正语义)。"""
        llm = _mock_llm()
        result = process_message(
            fresh_db, trace_id="V2-016-003",
            message_text="补打 ABC Reading +3 分",
            llm_call=llm,
        )
        assert result["status"] == "ok"
        assert "补打" in result["reply"]

    def test_更正_不调_LLM(self, fresh_db):
        """更正关键词 (同款修正语义)。"""
        llm = _mock_llm()
        result = process_message(
            fresh_db, trace_id="V2-016-004",
            message_text="更正: 晚睡扣 2 分应为扣 1 分",
            llm_call=llm,
        )
        assert result["status"] == "ok"
        assert "更正" in result["reply"]

    def test_修正_否定词放行(self, fresh_db):
        """「不需要修正」应放行让 LLM 解析, 不走 fast path。"""
        # 走 LLM 路径, mock 给一个合法的 record
        llm = _mock_llm(
            '{"intent": "record", "reasoning": "正常记账"}',
            '[{"type": "income", "amount": 1, "description": "数学口算"}]',
        )
        result = process_message(
            fresh_db, trace_id="V2-016-005",
            message_text="今天不需要修正任何东西, 数学口算加 1 分",
            llm_call=llm,
        )
        # 否定词在前 5 字内 → 放行, LLM 被调用, 走 record 路径
        assert result["status"] == "ok"
        # 应有 transactions 写入, 而不是 fast path 的引导文案
        assert "income/expense" not in result["reply"], \
            f"否定词应放行, 不应触发 fast path: {result['reply'][:200]}"


# ─── process_message: V2-005 缺金额(0 LLM 调用 mock) ───────────────────────

class TestNeedsAmount:
    """缺金额:不调 LLM 也能走通(因为 classify + parse 都 mock)。"""

    def test_全部缺金额_走_引导_不_记账(self, fresh_db):
        llm = _mock_llm(
            '{"intent": "record", "reasoning": "记账"}',  # classify
            '[{"type": "expense", "amount": null, "description": "买柠檬果饮"}]',  # parse
        )
        result = process_message(
            fresh_db, trace_id="NA-001",
            message_text="买柠檬果饮",
            llm_call=llm,
        )
        assert result["status"] == "ok"
        assert not result.get("items")
        assert "没听清金额" in result["reply"]
        assert "柠檬果饮" in result["reply"]

    def test_部分缺金额_记账后追加提示(self, fresh_db):
        llm = _mock_llm(
            '{"intent": "record"}',
            '[{"type": "income", "amount": 3, "description": "语文写字"},'
            ' {"type": "expense", "amount": null, "description": "ABC Reading 没读"}]',
            '"继续加油"',  # encourage
        )
        result = process_message(
            fresh_db, trace_id="NA-002",
            message_text="语文写字+3,ABC Reading 没读",
            llm_call=llm,
        )
        assert result["status"] == "ok"
        assert len(result["items"]) == 1
        assert result["items"][0]["amount"] == 3
        assert "没听清金额" in result["reply"]
        # needs_amount 透传
        assert len(result["needs_amount"]) == 1
        assert "ABC Reading" in result["needs_amount"][0]["description"]


# ─── process_message: V2-007 ref_id 注入 ──────────────────────────────────

class TestRefIdInjection:
    """所有产生的 tx 必须带 ref_id=trace_id。"""

    def test_单笔_tx_ref_id_等于_trace_id(self, fresh_db):
        llm = _mock_llm(
            '{"intent": "record"}',
            '[{"type": "income", "amount": 1, "description": "口算"}]',
            '"加油"',
        )
        process_message(
            fresh_db, trace_id="REF-001",
            message_text="口算加1分",
            llm_call=llm,
        )
        rows = fresh_db.execute(
            "SELECT ref_id, type, amount FROM transactions"
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["ref_id"] == "REF-001"

    def test_多笔_tx_全部带_ref_id(self, fresh_db):
        llm = _mock_llm(
            '{"intent": "record"}',
            '[{"type": "income", "amount": 1, "description": "口算"},'
            ' {"type": "expense", "amount": 3, "description": "买冰激凌"}]',
            '"加油"',
        )
        process_message(
            fresh_db, trace_id="REF-002",
            message_text="口算+1,买冰激凌-3",
            llm_call=llm,
        )
        rows = fresh_db.execute("SELECT ref_id FROM transactions").fetchall()
        assert all(r["ref_id"] == "REF-002" for r in rows), f"ref_id 不一致: {rows}"


# ─── process_message: audit_log.trace_id 全覆盖 ────────────────────────────

class TestAuditLogTraceId:
    """每次 process_message 后,所有 audit_log 记录的 trace_id 必须 == 传入 trace_id。"""

    def test_成功路径_所有_step_带_trace_id(self, fresh_db):
        llm = _mock_llm(
            '{"intent": "record"}',
            '[{"type": "income", "amount": 1, "description": "口算"}]',
            '"加油"',
        )
        process_message(
            fresh_db, trace_id="AUD-001",
            message_text="口算+1",
            llm_call=llm,
        )
        total = fresh_db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        with_tid = fresh_db.execute(
            "SELECT COUNT(*) FROM audit_log WHERE trace_id=?", ("AUD-001",)
        ).fetchone()[0]
        assert total > 0
        assert with_tid == total, f"audit_log.trace_id 覆盖率 {with_tid}/{total} ≠ 100%"

    def test_失败路径_也带_trace_id(self, fresh_db):
        """如果 LLM 抛错,所有 audit(包括失败)也得带 trace_id。"""
        def fail_llm(prompt):
            raise RuntimeError("模拟 LLM 失败")

        # 不期待内部异常 — 失败路径应该 catch 并返回 error status
        result = process_message(
            fresh_db, trace_id="AUD-002",
            message_text="测试",
            llm_call=fail_llm,
        )
        assert result["status"] == "error"
        # audit 仍要有 trace_id
        rows = fresh_db.execute(
            "SELECT step FROM audit_log WHERE trace_id=?", ("AUD-002",)
        ).fetchall()
        assert rows, "失败路径也必须有 audit 留痕"


# ─── process_message: trace_id 去重 ────────────────────────────────────────

class TestTraceIdDedup:
    """同一 trace_id 第二次调用应该 skipped。"""

    def test_重复_trace_id_第二次_skipped(self, fresh_db):
        llm = _mock_llm(
            '{"intent": "record"}',
            '[{"type": "income", "amount": 1, "description": "口算"}]',
            '"加油"',
        )
        r1 = process_message(
            fresh_db, trace_id="DUP-001",
            message_text="口算+1",
            llm_call=llm,
        )
        assert r1["status"] == "ok"
        # 第二次同 trace_id
        r2 = process_message(
            fresh_db, trace_id="DUP-001",
            message_text="其他消息",
            llm_call=llm,
        )
        assert r2["status"] == "skipped"


# ─── db 层: 事务原子性 ─────────────────────────────────────────────────────

class TestDBAtomicity:
    """insert_transactions_batch 原子性:多笔要么全成功,要么全回滚。"""

    def test_多笔_连续_balance_正确(self, fresh_db):
        insert_transactions_batch(fresh_db, [
            {"type": "income", "amount": 10, "description": "奖励"},
            {"type": "expense", "amount": -3, "description": "扣分"},
            {"type": "income", "amount": 5, "description": "再奖"},
        ])
        balance = get_current_balance(fresh_db)
        assert balance == 12, f"余额应 10-3+5=12,实际 {balance}"

    def test_空_batch_不报错(self, fresh_db):
        result = insert_transactions_batch(fresh_db, [])
        assert result == []


# ─── log_audit: trace_id 接受(0 LLM) ───────────────────────────────────────

class TestLogAuditSignature:
    """log_audit 必须接受 trace_id 参数。"""

    def test_签名_包含_trace_id(self):
        sig = inspect.signature(log_audit)
        assert "trace_id" in sig.parameters, f"log_audit 缺 trace_id: {list(sig.parameters)}"

    def test_默认_trace_id_为_None(self, fresh_db):
        """不传 trace_id 应该也能写(success=True)。"""
        log_audit(fresh_db, step="intake", input_summary="测试", success=True)
        row = fresh_db.execute(
            "SELECT trace_id FROM audit_log WHERE step='intake'"
        ).fetchone()
        assert row["trace_id"] is None

    def test_传_trace_id_写入(self, fresh_db):
        log_audit(fresh_db, step="intake", input_summary="测试", success=True, trace_id="T-LOG-001")
        row = fresh_db.execute(
            "SELECT trace_id FROM audit_log WHERE step='intake'"
        ).fetchone()
        assert row["trace_id"] == "T-LOG-001"


# ─── db 层: 锁 TTL ─────────────────────────────────────────────────────────

class TestProcessingLock:
    """锁的并发安全:TTL 过期后接管,COMPLETED 跳过,PROCESSING 阻塞。"""

    def test_首次_acquire_成功(self, fresh_db):
        ok = acquire_processing_lock(fresh_db, "LOCK-001", ttl_seconds=60, worker_id="w1")
        assert ok

    def test_重复_acquire_失败(self, fresh_db):
        acquire_processing_lock(fresh_db, "LOCK-002", ttl_seconds=60, worker_id="w1")
        ok2 = acquire_processing_lock(fresh_db, "LOCK-002", ttl_seconds=60, worker_id="w2")
        assert not ok2

    def test_release_后_能_重新_acquire(self, fresh_db):
        acquire_processing_lock(fresh_db, "LOCK-003", ttl_seconds=60, worker_id="w1")
        release_processing_lock(fresh_db, "LOCK-003")
        ok2 = acquire_processing_lock(fresh_db, "LOCK-003", ttl_seconds=60, worker_id="w2")
        assert ok2

    def test_TTL_过期_可接管(self, fresh_db):
        # TTL=0 立即过期
        acquire_processing_lock(fresh_db, "LOCK-004", ttl_seconds=0, worker_id="w1")
        ok2 = acquire_processing_lock(fresh_db, "LOCK-004", ttl_seconds=60, worker_id="w2")
        assert ok2, "TTL 过期应该可以接管"


# ─── is_message_processed / mark_message_processed ─────────────────────────

class TestMessageDedup:
    def test_首次_is_processed_返回_False(self, fresh_db):
        assert not is_message_processed(fresh_db, "DEDUP-001")

    def test_mark_后_is_processed_返回_True(self, fresh_db):
        mark_message_processed(fresh_db, trace_id="DEDUP-002")
        assert is_message_processed(fresh_db, "DEDUP-002")

    def test_mark_message_id_也能查(self, fresh_db):
        mark_message_processed(fresh_db, trace_id="DEDUP-003", message_id="MSG-X")
        assert is_message_processed(fresh_db, "DEDUP-003")
        assert is_message_processed(fresh_db, "DEDUP-003", message_id="MSG-X")


# ─── V2-008 撤销自然语言变种 ────────────────────────────────────────────────

class TestV008UndoVariants:
    """撤销/撤回/取消/作废 关键词命中走 fast path(0 LLM)。"""

    def test_自然语言撤销_走_fast_path(self, fresh_db):
        """原 45 条 idx 42:`积分消费 撤销笔误扣 2 分` → 不调 LLM"""
        llm = _mock_llm()  # 没人调用 → StopIteration
        result = process_message(
            fresh_db, trace_id="V008-001",
            message_text="积分消费 撤销笔误扣 2 分",
            llm_call=llm,
        )
        assert result["status"] == "ok"
        assert "不支持" in result["reply"]
        assert "撤销" in result["reply"] or "调账" in result["reply"]
        assert not result.get("items"), "撤销不应产生 tx"
        # audit 留痕 unsupported_intent
        rows = fresh_db.execute(
            "SELECT step FROM audit_log WHERE trace_id=?", ("V008-001",)
        ).fetchall()
        assert any(r[0] == "unsupported_intent" for r in rows)

    def test_撤回_关键词_也走_fast_path(self, fresh_db):
        llm = _mock_llm()
        result = process_message(
            fresh_db, trace_id="V008-002",
            message_text="撤回刚才的扣分",
            llm_call=llm,
        )
        assert result["status"] == "ok"
        assert "不支持" in result["reply"]

    def test_否定词_不撤销_放行调_LLM(self, fresh_db):
        """'今天不撤销任何东西' → 放行,让 LLM 解析"""
        llm = _mock_llm(
            '{"intent": "query"}',  # classify
            '{"type": "balance", "sql": "SELECT current_balance FROM config LIMIT 1"}',  # query
        )
        result = process_message(
            fresh_db, trace_id="V008-003",
            message_text="今天不撤销任何东西",
            llm_call=llm,
        )
        # 放行后至少应被 classify,不应走 unsupported_intent
        rows = fresh_db.execute(
            "SELECT step FROM audit_log WHERE trace_id=?", ("V008-003",)
        ).fetchall()
        steps = {r[0] for r in rows}
        assert "unsupported_intent" not in steps, f"否定词应放行,不应有 unsupported_intent: {steps}"
        # classify 步骤有
        assert "classify" in steps


# ─── V2-009 调账语法 ────────────────────────────────────────────────

class TestV009AdjustSyntax:
    """'调账' 关键词(前 10 字内)走 fast path,提示用 income/expense 形式。"""

    def test_调账开头_走_fast_path(self, fresh_db):
        """原 45 条 idx 11:`调账:修正看动画片 1 集扣分(应扣 -5 但扣了 -10,调账 +5)`"""
        llm = _mock_llm()
        result = process_message(
            fresh_db, trace_id="V009-001",
            message_text="调账:修正看动画片 1 集扣分(应扣 -5 但扣了 -10,调账 +5)",
            llm_call=llm,
        )
        assert result["status"] == "ok"
        assert "调账" in result["reply"] or "不支持" in result["reply"]
        assert not result.get("items")

    def test_调账_在描述中_也触发(self, fresh_db):
        """'今天我帮同学调账' → 调账就是要调账,触发 fast path"""
        llm = _mock_llm()
        result = process_message(
            fresh_db, trace_id="V009-002",
            message_text="今天我帮同学调账了一些积分",
            llm_call=llm,
        )
        assert result["status"] == "ok"
        assert "不支持" in result["reply"]
        # 应走 unsupported_intent
        rows = fresh_db.execute(
            "SELECT step FROM audit_log WHERE trace_id=?", ("V009-002",)
        ).fetchall()
        assert any(r[0] == "unsupported_intent" for r in rows)


# ─── V2-010 PARSE_RECORD_PROMPT 简化后 JSON 示例转义正确 ───────────────────────

class TestV010PromptJsonEscape:
    """PARSE_RECORD_PROMPT 用 {{ }} 转义,format(message=) 不报 KeyError。"""

    def test_PARSE_RECORD_PROMPT_format_不报_KeyError(self):
        """简化后的 prompt 仍能正常 .format(message='test')"""
        from runtime.pipeline import PARSE_RECORD_PROMPT
        try:
            formatted = PARSE_RECORD_PROMPT.format(message="口算加1分")
        except KeyError as e:
            pytest.fail(f"PARSE_RECORD_PROMPT.format() 报 KeyError({e}),说明 JSON 示例未用 {{}} 转义")

    def test_PARSE_RECORD_PROMPT_含_JSON_示例_没被占位符污染(self):
        """format 后 prompt 仍含 [{"type": 这种 JSON 字面"""
        from runtime.pipeline import PARSE_RECORD_PROMPT
        formatted = PARSE_RECORD_PROMPT.format(message="test")
        # 含 [{{ 转义后的 [
        assert '[{"type":' in formatted, f"format 后应含 JSON 示例:[{{\"type\": → {formatted[:200]}"
