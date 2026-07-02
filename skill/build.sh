#!/bin/bash
# build.sh - kids-points-v2 ClawHub release build (C-plan structure)
#
# 用法:
#   ./build.sh patch    # 2.0.0 → 2.0.1 (bugfix)
#   ./build.sh minor    # 2.0.0 → 2.1.0 (新功能)
#   ./build.sh major    # 2.0.0 → 3.0.0 (break change)
#   ./build.sh 2.3.0    # 指定版本号
#
# C-plan 目录结构:
#   ~/projects/kids-points-v2/           ← 项目根
#   ├── runtime/                          ← Python runtime
#   ├── skill/                            ← OpenClaw skill 包装层
#   │   ├── SKILL.md / agent-handler.js
#   │   ├── scripts/
#   │   └── build.sh (本文件)
#   └── extensions/                       ← 点阵屏等扩展
#
# 步骤:
#   1. 从 runtime/ 拉一份干净的副本（排除 db / 内部资料）
#   2. 脱敏: config.yaml → config.yaml.example
#   3. 更新 VERSION + CHANGELOG
#   4. tar.gz 打包 → skill/release/ (用于 clawhub publish)

set -euo pipefail

# ─── 配置 ───────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$SCRIPT_DIR"
PROJECT_ROOT="$(dirname "$SKILL_ROOT")"    # 项目根（kids-points-v2/）
RUNTIME_ROOT="$PROJECT_ROOT/runtime"
BUILD_DIR="$SKILL_ROOT/build"
VERSION_FILE="$SKILL_ROOT/VERSION"

# ─── 检查 git 状态 ────────────────────────────────────────
if ! git diff --quiet HEAD 2>/dev/null; then
  echo "❌ git dirty. commit 后再 build"
  exit 1
fi

# ─── 解析版本号 ────────────────────────────────────────────
BUMP="${1:-patch}"
CURRENT="${CURRENT:-$(cat "$VERSION_FILE" 2>/dev/null || echo "2.0.0")}"

IFS='.' read -ra V <<< "$CURRENT"
MAJOR="${V[0]:-0}"
MINOR="${V[1]:-0}"
PATCH="${V[2]:-0}"

case "$BUMP" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0;;
  minor) MINOR=$((MINOR + 1)); PATCH=0;;
  patch) PATCH=$((PATCH + 1));;
  *)
    if [[ "$BUMP" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      NEW_VERSION="$BUMP"
    else
      echo "❌ 版本参数错误: $BUMP (用 major|minor|patch 或 X.Y.Z)"
      exit 1
    fi
    ;;
esac

NEW_VERSION="${NEW_VERSION:-$MAJOR.$MINOR.$PATCH}"
echo "📦 版本: $CURRENT → $NEW_VERSION"

# ─── Step 1: 准备 build/ ────────────────────────────────────
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# ─── Step 2: 复制 skill 文件 ─────────────────────────────────
for f in SKILL.md README.md LICENSE agent-handler.js scripts build.sh VERSION CHANGELOG.md; do
  if [ -e "$SKILL_ROOT/$f" ]; then
    cp -r "$SKILL_ROOT/$f" "$BUILD_DIR/"
  fi
done

# ─── Step 3: 复制脱敏 runtime ────────────────────────────────
RT_BUILD="$BUILD_DIR/runtime"
mkdir -p "$RT_BUILD/data"

# 产品代码（不复制 db / 内部资料）
for f in cli.py db.py pipeline.py llm_config.py; do
  if [ -f "$RUNTIME_ROOT/$f" ]; then
    cp "$RUNTIME_ROOT/$f" "$RT_BUILD/$f"
  fi
done

# config.yaml.example（脱敏模板）
if [ -f "$RUNTIME_ROOT/config.yaml.example" ]; then
  cp "$RUNTIME_ROOT/config.yaml.example" "$RT_BUILD/config.yaml.example"
fi

# data/ 占位（生产 db 不打包）
touch "$RT_BUILD/data/.gitkeep"

# ─── Step 4: 更新 VERSION + CHANGELOG ─────────────────────────
echo "$NEW_VERSION" > "$BUILD_DIR/VERSION"
echo "$NEW_VERSION" > "$SKILL_ROOT/VERSION"

CHANGELOG="$BUILD_DIR/CHANGELOG.md"
if [ ! -f "$CHANGELOG" ]; then
  cat > "$CHANGELOG" <<'EOF'
# kids-points-v2 Changelog

All notable changes to this project will be documented in this file.
EOF
fi

echo "" >> "$CHANGELOG"
echo "## v$NEW_VERSION ($(date +%Y-%m-%d))" >> "$CHANGELOG"
echo "" >> "$CHANGELOG"
echo "### Changed" >> "$CHANGELOG"
echo "- (build 阶段手动填写)" >> "$CHANGELOG"
echo "" >> "$CHANGELOG"

# ─── Step 5: tar.gz 打包 ────────────────────────────────────
TARBALL="$SKILL_ROOT/release/kids-points-v2-$NEW_VERSION.tar.gz"
mkdir -p "$SKILL_ROOT/release"

cd "$BUILD_DIR"
tar -C "$BUILD_DIR" --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' -czf "$TARBALL" .
cd "$SKILL_ROOT"

echo ""
echo "✅ Build 完成"
echo "   tarball: $TARBALL"
echo "   build/:  $BUILD_DIR"
echo ""
echo "下一步:"
echo "  1. 检查 build/: ls -la $BUILD_DIR/"
echo "  2. 确认 tarball: tar -tzf $TARBALL | head -20"
echo "  3. 发布: clawhub publish $BUILD_DIR --slug kids-points-v2 --version $NEW_VERSION"