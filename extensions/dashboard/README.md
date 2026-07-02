# 儿童积分看板 (Kids Points Dashboard)

> 桌面积分看板 — ESP32 + LED 矩阵单元板 + Flask server，只读 kids-points-v2 积分数据。

## 位置

```
~/projects/kids-points-v2/extensions/dashboard/
├── code/
│   ├── server/      ← Flask + watchdog + in-memory cache
│   ├── esp32/       ← ESP32 固件（HUB75 LED 驱动）
│   └── sim/         ← pygame 仿真（不通硬件直接调字号/排版）
├── docs/            ← 设计/架构/硬件/验证文档
└── kanban.md / notes.md
```

## 数据源

`server/data_source.py` 指向 kids-points-v2 新路径：
- `V2_CLI`: `/home/wang/projects/kids-points-v2/runtime/cli.py`
- `V2_DB`: `/home/wang/projects/kids-points-v2/runtime/data/kids_points.db`

## 部署

1. 安装依赖：`pip install flask watchdog flask-sock`
2. 运行 server：`python3 code/server/server.py`
3. 烧录固件：参考 `code/esp32/desktop/README.md`
4. systemd 自启：`systemctl enable --now dashboard`

## 文档入口

- `docs/INDEX.md` — 按场景查文档
- `docs/plan.md` — 完整设计文档
- `docs/verify.md` — 验证手册 + FAQ
- `docs/hardware.md` — 硬件清单 + 接线