# BUGS — kids-points-v2 已知 bug + 修复归档

> 模式: **根因 + 修复 + 验证 + commit**。每个 bug 一个 section。
> 修复完的 bug 标 ✅ (含 commit / PR link)；未修的标 ⚠️ (含 workaround)。

---

## ✅ 2026-07-05 — V2 CLI 永远 ImportError, 看板数据断层数天

### 症状
- 7/4 02:03 systemd TERM 掉 `dashboard.service` 后, 看板没成功重启
- 之后 ESP32 拉 `/api/dashboard` 全靠 `/tmp/dashboard_cache.json` 兜底 (7/4 20:56 快照, 含 5 行流水)
- 7/4 后任何 V2 写入 (积分变动/流水) 都不同步到屏

### 根因 (两个独立 bug, 都拦住 V2 CLI 启动)

#### Bug A: `runtime/cli.py` 第 33 行死导入

`5cfda3e` commit 老王把 `from db / from pipeline` 改成了相对导入 (`from .db / from .pipeline`), 但**漏改 `from reports import generate_daily_report, generate_monthly_report` 这行**。`reports/` 是仓库根的报告产物目录 (含 4 个 .md + `v1_v2_compare.py`), 没 `__init__.py`, 这两个函数本仓库也无定义 (全 worktree grep 0 命中)。

**后果**: 任何调 `cli.py` 的路径都 `ImportError: cannot import name 'generate_daily_report' from 'reports' (unknown location)`, 看板 / 飞书消息 / CLI 交互全部 100% 失败。

**为什么测试没发现**: `tests/test_pipeline_unit.py` 只 `from runtime.db import ...`, 不导入 `cli.py`。老王看到 pytest 60 passed 就以为 OK, 但 CLI 实际从来没启动成功过。

#### Bug B: `data_source.py` 等三处 subprocess 调用模式错

老王写 `data_source.cli_call()` 时, 用 `subprocess.run(["python3", "/abs/path/cli.py", "balance"])`, 把 cli.py 当**脚本**跑 (`__name__ == "__main__"`, 没有 `__package__`)。即使 Bug A 修了, 这种调用模式也跑不通 `from .db` 相对导入。

**踩坑位置**: `extensions/dashboard/code/server/data_source.py` / `sim/desktop_sim.py` / `skill/scripts/handle_feishu.py` 三处同代码。

### 修复

| 文件 | 改法 |
|---|---|
| `runtime/cli.py` | 删 `from reports import ...`; 加 `_try_import_reports()` 懒加载 + `cmd_reports_daily()` / `cmd_reports_monthly()`; `--daily`/`--monthly` 找不到 reports 包返 exit 1 + 友好提示 |
| `extensions/dashboard/code/server/data_source.py` | subprocess 改 `python3 -m runtime.cli <subcmd>` + `cwd=V2_PROJECT_ROOT` |
| `extensions/dashboard/code/sim/desktop_sim.py` | 同上 |
| `skill/scripts/handle_feishu.py` | 加 `V2_PROJECT_ROOT` 常量 + subprocess 同改 |
| `tests/test_cli_subprocess.py` (新) | 5 个回归测试, 0 LLM token, 秒级, 覆盖 3 个子命令 + ImportError 检测 + module 级 cli_call 包装 |
| `extensions/dashboard/docs/CHANGELOG.md` | 加 v5.5 段 |

### 验证 (2026-07-05)

- ✅ 5/5 新回归测试通过 (`python3 tests/test_cli_subprocess.py`)
- ✅ 60/60 既有 `test_pipeline_unit.py` 通过 (无破坏)
- ✅ 前台 `python3 -m runtime.cli balance/today/history` 全 OK, 中文流水正常
- ✅ systemd `dashboard.service` `active (running)`, `/api/dashboard` 返真数据 (balance=24.5, 5 行流水), `/health` `cache.dirty=false, watchdog_alive=true`
- ✅ ESP32 `192.168.50.197` 已经在 5s 一次拉, journal 全 200

### 老王决策

- 用**最小 surgical 修复**: 不重写 cli.py / pipeline.py 结构, 只改 subprocess 调用 + 懒加载 reports, 跟"够用就好"一致
- 真实根因修复, 不靠 cache 兜底 (cache 保留作 v5.4 设计原则)

### Commit / PR

- 分支: `fix/dashboard-v2-import-path`
- (待老王手动看板子确认后 push + PR)