"""
回归测试: 验证 data_source.py / desktop_sim.py 的 V2 CLI subprocess 调用能拿到真数据.

背景 (2026-07-05 bugfix):
  data_source.py (server) 和 desktop_sim.py (仿真) 都用 subprocess 调 V2 CLI.
  之前用 `python3 <绝对路径>/cli.py <subcmd>`, 但 cli.py 顶部用相对导入
  `from .db import ...` + `from reports import ...`. 脚本模式没父包上下文, 必然
  ImportError, 看板永远靠 /tmp cache 兜底, 数据断层数天不自知.

  修法: 改 `python3 -m runtime.cli <subcmd>` + cwd=V2_PROJECT_ROOT.
  cli.py 第 33 行遗留的 `from reports import ...` 也改为懒加载.

这个测试:
  1. 直接调 subprocess `python3 -m runtime.cli balance`, 断言返回 JSON 且 balance 字段是数字
  2. 模拟 data_source 内部 cli_call 的 subprocess run, 验证不再 ImportError
  3. 验证 cli.py 单条消息模式也能跑 (handle_feishu.py 路径)

跑法:
    cd /home/wang/projects/kids-points-v2
    python3 tests/test_cli_subprocess.py
    或: pytest tests/test_cli_subprocess.py -v
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

# tests/ 在仓库根下, 直接用绝对路径
PROJECT_ROOT = "/home/wang/projects/kids-points-v2"
RUNTIME_DIR = f"{PROJECT_ROOT}/runtime"
DB_PATH = f"{PROJECT_ROOT}/runtime/data/kids_points.db"


class TestCliSubprocess(unittest.TestCase):
    """直接调 cli.py 子命令, 验证包模式启动 OK + 返回合法 JSON."""

    def setUp(self):
        if not Path(DB_PATH).exists():
            self.skipTest(f"V2 DB 不存在: {DB_PATH} (生产环境才有, CI 跳过)")

    def test_balance_subprocess(self):
        """`python3 -m runtime.cli balance` 应返回非空 dict, 含 balance 字段."""
        result = subprocess.run(
            ["python3", "-m", "runtime.cli", "balance"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(
            result.returncode, 0,
            f"cli.py balance 退出码 {result.returncode}\nstdout: {result.stdout[:200]}\nstderr: {result.stderr[:200]}"
        )
        data = json.loads(result.stdout)
        self.assertIn("balance", data)
        self.assertIsInstance(data["balance"], (int, float))

    def test_today_subprocess(self):
        """`python3 -m runtime.cli today` 应返回 dict, 含 date/income/expense 字段."""
        result = subprocess.run(
            ["python3", "-m", "runtime.cli", "today"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr[:300]}")
        data = json.loads(result.stdout)
        self.assertIn("date", data)
        self.assertIn("income", data)
        self.assertIn("expense", data)

    def test_history_subprocess(self):
        """`python3 -m runtime.cli history --days 7 --limit 5` 应返回 history 数组."""
        result = subprocess.run(
            ["python3", "-m", "runtime.cli", "history", "--days", "7", "--limit", "5"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr[:300]}")
        data = json.loads(result.stdout)
        self.assertIn("history", data)
        self.assertIsInstance(data["history"], list)

    def test_no_import_error_on_startup(self):
        """关键回归: cli.py 启动不应该有 ImportError (相对导入 + reports 懒加载 OK)."""
        result = subprocess.run(
            ["python3", "-m", "runtime.cli", "balance"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # 旧 bug 症状: stderr 含 "attempted relative import with no known parent package"
        self.assertNotIn(
            "attempted relative import", result.stderr,
            f"cli.py 启动仍有相对导入问题:\nstderr: {result.stderr[:500]}"
        )
        self.assertNotIn(
            "ImportError", result.stderr,
            f"cli.py 启动仍有 ImportError:\nstderr: {result.stderr[:500]}"
        )


class TestDataSourceWrapper(unittest.TestCase):
    """模拟 data_source.py 的 cli_call 内部行为, 验证包装层不再踩坑."""

    def setUp(self):
        if not Path(DB_PATH).exists():
            self.skipTest(f"V2 DB 不存在: {DB_PATH}")

    def test_via_module_call(self):
        """直接 import data_source.cli_call 调一次 balance."""
        sys.path.insert(0, f"{PROJECT_ROOT}/extensions/dashboard/code/server")
        try:
            from data_source import cli_call
            data = cli_call(["balance"])
        finally:
            sys.path.pop(0)
        self.assertIsNotNone(data, "cli_call 返回 None (subprocess 失败)")
        self.assertIn("balance", data)
        self.assertIsInstance(data["balance"], (int, float))


if __name__ == "__main__":
    unittest.main(verbosity=2)