# kids-points-v2

儿童积分管理工具 V2 — SQLite 存储 + LLM 语义分析 + CLI 接口。

## 快速开始

```bash
# 配置 LLM（复制示例配置）
cp runtime/config.yaml.example runtime/config.yaml
# 编辑 config.yaml 填入你的 LLM 信息

# 查余额
python3 runtime/cli.py balance

# 记录积分
python3 runtime/cli.py "今天数学加 1 分"
```

详细文档见 [SKILL.md](skill/SKILL.md)。

## 分支策略

| 分支 | 内容 | 用途 |
|------|------|------|
| **main** | 开源安全版（`config.yaml.example` + 产品代码） | GitHub 主分支、ClawHub 发布 |
| **dev** | 自用版（真实配置 + 内部资料 + 测试数据） | 本地开发，不推送 |

## 扩展

- 点阵屏看板：`extensions/dashboard/`

## 开源

- GitHub: [github.com/cowboy231/kids-points-v2](https://github.com/cowboy231/kids-points-v2)
- License: MIT

_用心记录每一次进步。_ 🌟