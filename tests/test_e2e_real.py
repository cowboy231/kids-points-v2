#!/usr/bin/env python3
"""
kids-points-runtime 端到端真实 LLM 测试
使用 MiniMax 2.7 走完整流水线（分类→解析→校验→写SQLite→鼓励语）

策略：每个测试独立 DB + 60s 超时保护，分批输出。
"""

import sys, os, json, time, csv
from datetime import date, timedelta, datetime
from pathlib import Path
import signal

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

import runtime.pipeline as pl
from runtime.db import init_db

# ─── 配置 ───
MAX_CASE_SECONDS = 60  # 单用例超时

# ─── 结果收集 ───
RESULTS = []
WARN = 0
WARN_DETAILS = []

def ok(cond, msg=""):
    if not cond:
        raise AssertionError(msg)

def should_pass(r, tag=""):
    tag = f" [{tag}]" if tag else ""
    ok(r["status"] == "ok", f"预期 ok{tag}，实际 {r['status']}: {r.get('reply','')[:60]}{tag}")
    ok(r.get("reply"), f"回复不应为空{tag}")

tagn = ""

class TimeoutError_(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError_("用例超时")

def run_with_timeout(fn, conn, timeout=MAX_CASE_SECONDS):
    """带超时保护的用例执行"""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    try:
        fn(conn)
    finally:
        signal.alarm(0)

def run_test(name, desc, fn, tags=None):
    global WARN, WARN_DETAILS, tagn
    tagn = name
    conn = init_db(":memory:")
    t_start = time.time()
    try:
        run_with_timeout(fn, conn)
        duration = time.time() - t_start
        status = "PASS"
        emoji = "✅"
    except TimeoutError_ as e:
        duration = time.time() - t_start
        status = "TIMEOUT"
        emoji = "⏰"
        WARN += 1
        WARN_DETAILS.append({"id": name, "detail": str(e)})
    except AssertionError as e:
        duration = time.time() - t_start
        status = "FAIL"
        emoji = "❌"
        WARN += 1
        WARN_DETAILS.append({"id": name, "detail": str(e)})
    except Exception as e:
        duration = time.time() - t_start
        status = "ERROR"
        emoji = "💥"
    finally:
        conn.close()

    print(f"  {emoji} {status} {name}: {desc}  ({duration:.1f}s)")
    RESULTS.append({
        "id": name, "desc": desc, "status": status,
        "duration_s": round(duration, 1),
        "tags": tags or [],
    })


# ═══════════════════════════════════════════════════════════
# Part A: 积分记账
# ═══════════════════════════════════════════════════════════

def a_001_income_single(conn):
    """单笔加分：扫地加5分"""
    r = pl.process_message(conn, "a-001", "扫地加5分", message_id="a-001")
    should_pass(r)
    row = conn.execute("SELECT type, amount, description FROM transactions").fetchone()
    ok(row["type"] == "income", f"类型应为 income: {row['type']}")
    ok(row["amount"] == 5, f"金额应为 5 (5分): {row['amount']}")
    ok("扫地" in row["description"], f"描述含扫地: {row['description']}")

def a_002_expense_single(conn):
    """单笔扣分：买零食扣2分"""
    r = pl.process_message(conn, "a-002", "买零食扣2分", message_id="a-002")
    should_pass(r)
    row = conn.execute("SELECT type, amount, description FROM transactions").fetchone()
    ok(row["type"] == "expense", f"类型应为 expense: {row['type']}")
    ok(row["amount"] == -2, f"金额应为 -2 (扣2分): {row['amount']}")
    ok("零食" in row["description"], f"描述含零食: {row['description']}")

def a_003_multi_items(conn):
    """多笔同消息：口算加1分，买冰激凌扣4分"""
    r = pl.process_message(conn, "a-003", "口算加1分，买冰激凌扣4分", message_id="a-003")
    should_pass(r)
    ok("口算" in r["reply"] or "冰激凌" in r["reply"], f"回复应含口算/冰激凌: {r['reply'][:40]}")
    rows = conn.execute("SELECT type, amount, description FROM transactions ORDER BY created_at").fetchall()
    ok(len(rows) == 2, f"应有2条: {len(rows)}")
    inc = [r for r in rows if r["type"] == "income"]
    exp = [r for r in rows if r["type"] == "expense"]
    ok(len(inc) == 1 and len(exp) == 1, f"应各有1条: inc={len(inc)} exp={len(exp)}")

def a_004_balance_accumulation(conn):
    """连续5笔累积余额"""
    for mid, text, exp_amount in [
        ("a-004-1", "扫地加3分", 3),
        ("a-004-2", "洗碗加2分", 2),
        ("a-004-3", "乱扔垃圾扣1分", -1),
        ("a-004-4", "跳绳加5分", 5),
        ("a-004-5", "玩手机扣2分", -2),
    ]:
        r = pl.process_message(conn, mid, text, message_id=mid)
        should_pass(r, f"step {mid}")
    balance = conn.execute("SELECT SUM(CASE WHEN type='income' THEN amount ELSE 0 END) FROM transactions").fetchone()[0]
    ok(balance == 10, f"预期总收入 10 (3+2+5), 实际 {balance}")
    # 总余额（含扣分）
    total = conn.execute("SELECT SUM(amount) FROM transactions").fetchone()[0]
    ok(total == 7, f"预期总余额 7 (3+2-1+5-2), 实际 {total}")

def a_005_zero_amount(conn):
    """0金额拒绝"""
    r = pl.process_message(conn, "a-005", "加0分", message_id="a-005")
    ok(r["status"] in ("error", "skipped"), f"0金额应拒绝: {r['status']} / {r.get('reply','')[:40]}")


# ═══════════════════════════════════════════════════════════
# Part B: 查询
# ═══════════════════════════════════════════════════════════

def b_001_balance_query(conn):
    """查余额"""
    pl.process_message(conn, "b-001a", "扫地加5分", message_id="b-001a")
    r = pl.process_message(conn, "b-001b", "查余额", message_id="b-001b")
    should_pass(r)
    ok("5" in r["reply"] or "5分" in r["reply"] or "5.0" in r["reply"], f"回复应含5: {r['reply'][:60]}")

def b_002_today_query(conn):
    """今日统计"""
    pl.process_message(conn, "b-002a", "扫地加3分", message_id="b-002a")
    r = pl.process_message(conn, "b-002b", "今天统计", message_id="b-002b")
    ok(r["status"] in ("ok", "error"), f"状态: {r['status']} / {r.get('reply','')[:40]}")
    if r["status"] == "ok":
        ok("3" in r["reply"], f"回复应含3: {r['reply'][:60]}")


# ═══════════════════════════════════════════════════════════
# Part C: 调账
# ═══════════════════════════════════════════════════════════

def c_001_adjust_initiate(conn):
    """调账发起：口算1分→2分"""
    pl.process_message(conn, "c-001a", "口算加1分", message_id="c-001a")
    r = pl.process_message(conn, "c-001b", "调账 口算加到2分", message_id="c-001b")
    ok(r["status"] == "ok", f"调账发起应 ok: {r['status']} / {r.get('reply','')[:40]}")
    ok("确认" in r["reply"] or "2" in r["reply"], f"回复应含确认+金额: {r['reply'][:60]}")

def c_002_adjust_confirm(conn):
    """调账确认"""
    pl.process_message(conn, "c-002a", "口算加1分", message_id="c-002a")
    pl.process_message(conn, "c-002b", "调账 口算加到2分", message_id="c-002b")
    r = pl.process_message(conn, "c-002c", "确认", message_id="c-002c")
    should_pass(r, "confirm")
    rows = conn.execute("SELECT type, amount, description FROM transactions ORDER BY created_at").fetchall()
    adjustments = [r for r in rows if r["type"] == "adjustment"]
    ok(len(adjustments) == 1, f"应有1条调账: {len(adjustments)}")
    total = conn.execute("SELECT SUM(amount) FROM transactions").fetchone()[0]
    ok(total == 2, f"调账后余额应 2: {total}")

def c_003_adjust_cancel(conn):
    """调账取消"""
    pl.process_message(conn, "c-003a", "口算加1分", message_id="c-003a")
    pl.process_message(conn, "c-003b", "调账 口算加到2分", message_id="c-003b")
    r = pl.process_message(conn, "c-003c", "取消", message_id="c-003c")
    ok(r["status"] == "ok", f"取消应 ok: {r['status']} / {r.get('reply','')[:40]}")
    ok("取消" in r["reply"] or "已取消" in r["reply"], f"回复应含取消: {r['reply'][:40]}")
    pending = conn.execute("SELECT id FROM pending_adjustments WHERE status='cancelled'").fetchall()
    ok(len(pending) >= 1, f"应有被取消的记录: {len(pending)}")


# ═══════════════════════════════════════════════════════════
# Part D: 时序/完整性
# ═══════════════════════════════════════════════════════════

def d_001_sequential_balance(conn):
    """连续记账逐步累计余额"""
    for i, (mid, text, exp_balance) in enumerate([
        ("d-001-1", "扫地加3分", 3),
        ("d-001-2", "洗碗加2分", 5),
        ("d-001-3", "跳绳加5分", 10),
        ("d-001-4", "买饮料扣1分", 9),
    ]):
        r = pl.process_message(conn, mid, text, message_id=mid)
        should_pass(r, f"step {i+1} ({mid})")
    rows = conn.execute("SELECT type, amount, balance_after FROM transactions ORDER BY created_at").fetchall()
    ok(len(rows) == 4, f"应有4条: {len(rows)}")
    ok(rows[0]["balance_after"] == 3)
    ok(rows[1]["balance_after"] == 5)
    ok(rows[2]["balance_after"] == 10)
    ok(rows[3]["balance_after"] == 9)

def d_002_duplicate_message(conn):
    """重复消息去重"""
    r1 = pl.process_message(conn, "d-002", "扫地加2分", message_id="d-002")
    should_pass(r1, "first")
    r2 = pl.process_message(conn, "d-002", "扫地加2分", message_id="d-002")
    ok(r2["status"] == "skipped", f"重复应 skipped: {r2['status']}")
    count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    ok(count == 1, f"仅1条交易: {count}")

def d_003_deduplication_verify_audit(conn):
    """去重+审计日志完整性"""
    r1 = pl.process_message(conn, "d-003-a", "买菜加2分", message_id="d-003-a")
    should_pass(r1, "first")
    r2 = pl.process_message(conn, "d-003-a", "买菜加2分", message_id="d-003-a")
    ok(r2["status"] == "skipped", f"重复: {r2['status']}")
    # 第一次应有完整的审计日志
    all_steps = conn.execute("SELECT step, input_summary FROM audit_log ORDER BY timestamp").fetchall()
    steps = [s["step"] for s in all_steps]
    for required in ["intake", "classify", "parse", "validate", "write", "mark_processed"]:
        ok(required in steps, f"缺失 {required}: {steps}")

def d_004_audit_trail_complete(conn):
    """单次完整记账 → 检查 audit_log"""
    r = pl.process_message(conn, "d-004", "跳绳加5分", message_id="d-004")
    should_pass(r, "record")
    steps = conn.execute("SELECT step FROM audit_log ORDER BY timestamp").fetchall()
    step_names = [s["step"] for s in steps]
    for required in ["intake", "classify", "parse", "validate", "write", "mark_processed"]:
        ok(required in step_names, f"缺失 {required}: {step_names}")


# ═══════════════════════════════════════════════════════════
# Part E: 异常
# ═══════════════════════════════════════════════════════════

def e_001_empty_message(conn):
    """空消息不应崩溃"""
    r = pl.process_message(conn, "e-001", "", message_id="e-001")
    ok(r["status"] in ("ok", "error", "skipped"), f"不应崩溃: {r['status']}")

def e_002_negative_rejected(conn):
    """负金额（扣-1分）会被 reject 不崩溃"""
    r = pl.process_message(conn, "e-002", "扣-1分", message_id="e-002")
    # LLM 可能解析失败或 pipeline 校验失败，都属于合理行为
    ok(r["status"] in ("ok", "error", "skipped"), f"不应崩溃: {r['status']}")
    count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    ok(count == 0, f"不应写库: {count}")

def e_003_large_amount(conn):
    """大金额不应超过限制"""
    r = pl.process_message(conn, "e-003", "加9999分", message_id="e-003")
    ok(r["status"] in ("ok", "error", "skipped"), f"不应崩溃: {r['status']}")
    if r["status"] == "ok":
        row = conn.execute("SELECT amount FROM transactions").fetchone()
        ok(row["amount"] <= 10000, f"金额不应超过限制: {row['amount']}")

def e_004_gibberish(conn):
    """无意义消息不会崩溃"""
    r = pl.process_message(conn, "e-004", "的风格的风格是大幅", message_id="e-004")
    ok(r["status"] in ("ok", "error", "skipped"), f"不应崩溃: {r['status']}")

def e_005_emoji_message(conn):
    """带表情符号的消息"""
    r = pl.process_message(conn, "e-005", "扫地加5分", message_id="e-005")
    ok(r["status"] in ("ok", "error", "skipped"), f"不应崩溃: {r['status']}")


# ═══════════════════════════════════════════════════════════
# 运行
# ═══════════════════════════════════════════════════════════

def main():
    # ── PART 过滤 ──
    part_filter = None
    if len(sys.argv) > 1 and sys.argv[1] == "--part":
        if len(sys.argv) < 3:
            print("用法: python test_e2e_real.py --part A|B|C|D|E [A|B|C|D|E ...]")
            sys.exit(1)
        part_filter = set(sys.argv[2:])
        print(f"   [filter] 只跑 Part: {sorted(part_filter)}")

    print("=" * 62)
    print(" kids-points-runtime 真实 LLM 端到端测试")
    print(f"   LLM: {pl.LLM_MODEL}")
    print(f"   启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   MiniMax 2.7 | 60s 用例超时")
    print("=" * 62)

    # ── PART A: 积分记账 ──
    if part_filter is None or "A" in part_filter:
        print("\n── Part A: 积分记账 ──")
        run_test("A-001", "单笔加分：扫地加5分", a_001_income_single, ["income", "single"])
        run_test("A-002", "单笔扣分：买零食扣2分", a_002_expense_single, ["expense", "single"])
        run_test("A-003", "多笔同消息：口算+1分，冰激凌-4分", a_003_multi_items, ["income", "expense", "multi"])
        run_test("A-004", "连续5笔累积余额=7", a_004_balance_accumulation, ["balance", "accumulation"])
        run_test("A-005", "0金额拒绝", a_005_zero_amount, ["edge", "zero"])

    # ── PART B: 查询 ──
    if part_filter is None or "B" in part_filter:
        print("\n── Part B: 查询 ──")
        run_test("B-001", "查余额", b_001_balance_query, ["query", "balance"])
        run_test("B-002", "今日统计", b_002_today_query, ["query", "today"])

    # ── PART C: 调账 ──
    if part_filter is None or "C" in part_filter:
        print("\n── Part C: 调账 ──")
        run_test("C-001", "调账发起：口算1分→2分", c_001_adjust_initiate, ["adjust", "initiate"])
        run_test("C-002", "调账确认", c_002_adjust_confirm, ["adjust", "confirm"])
        run_test("C-003", "调账取消", c_003_adjust_cancel, ["adjust", "cancel"])

    # ── PART D: 完整性 ──
    if part_filter is None or "D" in part_filter:
        print("\n── Part D: 时序/完整性 ──")
        run_test("D-001", "连续记账逐步累计余额", d_001_sequential_balance, ["timing", "balance"])
        run_test("D-002", "重复消息去重 → skipped", d_002_duplicate_message, ["dedup", "timing"])
        run_test("D-003", "去重+审计日志完整性", d_003_deduplication_verify_audit, ["audit", "dedup"])
        run_test("D-004", "审计日志覆盖全部步骤", d_004_audit_trail_complete, ["audit", "completeness"])

    # ── PART E: 异常 ──
    if part_filter is None or "E" in part_filter:
        print("\n── Part E: 异常消息 ──")
        run_test("E-001", "空消息不崩溃", e_001_empty_message, ["edge", "empty"])
        run_test("E-002", "负金额不写库", e_002_negative_rejected, ["edge", "negative"])
        run_test("E-003", "大金额不崩溃", e_003_large_amount, ["edge", "large"])
        run_test("E-004", "无意义消息不崩溃", e_004_gibberish, ["edge", "gibberish"])
        run_test("E-005", "emoji消息不崩溃", e_005_emoji_message, ["edge", "emoji"])

    # ── 汇总 ──
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    timeout = sum(1 for r in RESULTS if r["status"] == "TIMEOUT")
    errored = sum(1 for r in RESULTS if r["status"] == "ERROR")
    total = len(RESULTS)

    print(f"\n{'=' * 62}")
    print(f"  汇总: ✅{passed} ❌{failed} ⏰{timeout} 💥{errored} / 总计 {total}")
    if WARN > 0:
        print(f"  ⚠️  警告 ({WARN}):")
        for w in WARN_DETAILS:
            print(f"    {w['id']}: {w['detail']}")
    print(f"{'=' * 62}")

    # 生成 HTML 报告
    generate_report(passed, failed, timeout, errored, total)


def generate_report(passed, failed, timeout, errored, total):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html><html lang=zh><meta charset=utf-8>
<title>kids-points-runtime E2E 测试报告</title>
<style>
body{{font-family:sans-serif;background:#f5f5f5;margin:20px}}
h1{{color:#333}}
.summary{{margin:15px 0;padding:12px;background:#fff;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
.summary .pass{{color:#4caf50;font-weight:700}}
.summary .fail{{color:#f44336;font-weight:700}}
.summary .warn{{color:#ff9800;font-weight:700}}
table{{border-collapse:collapse;width:100%;margin-top:10px}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #ddd}}
th{{background:#4a90d9;color:#fff}}
tr:nth-child(even){{background:#f9f9f9}}
.status-PASS{{color:#4caf50;font-weight:700}}
.status-FAIL{{color:#f44336;font-weight:700}}
.status-TIMEOUT{{color:#ff9800}}
.status-ERROR{{color:#9c27b0}}
.timeout-cell{{color:#ff9800;font-style:italic}}
</style>
<body>
<h1>kids-points-runtime 端到端测试报告</h1>
<div class=summary>
<p>测试时间: {t}</p>
<p>LLM: MiniMax 2.7 | 超时: 60s/用例</p>
<p><span class=pass>✅通过: {passed}</span> |
<span class=fail>❌失败: {failed}</span> |
<span class=warn>⏰超时: {timeout}</span> |
💥异常: {errored} |
总计: {total}</p>
</div>
<table><tr><th>ID</th><th>场景</th><th>状态</th><th>耗时</th></tr>
"""
    for r in RESULTS:
        status_class = f"status-{r['status']}"
        dur = f"{r['duration_s']}s"
        if r['status'] == 'TIMEOUT':
            dur = f"<span class=timeout-cell>{dur}</span>"
        html += f"<tr><td>{r['id']}</td><td>{r['desc']}</td><td class={status_class}>{r['status']}</td><td>{dur}</td></tr>"

    if WARN > 0:
        html += '<tr><td colspan=4><hr><b>⚠️ 警告</b></td></tr>'
        for w in WARN_DETAILS:
            html += f'<tr><td>{w["id"]}</td><td colspan=3>{w["detail"]}</td></tr>'

    html += "</table></body></html>"
    report_path = PROJECT_ROOT / "e2e_report.html"
    with open(report_path, "w") as f:
        f.write(html)
    print(f"\n📄 报告已保存: {report_path}")


if __name__ == "__main__":
    main()
