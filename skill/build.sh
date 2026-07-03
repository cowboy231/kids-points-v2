#!/bin/bash
# build.sh - kids-points-v2 ClawHub release build
#
# 用法:
#   ./build.sh patch                    # 2.0.0 → 2.0.1 (bugfix)
#   ./build.sh minor                    # 2.0.0 → 2.1.0 (新功能)
#   ./build.sh major                    # 2.0.0 → 3.0.0 (break change)
#   ./build.sh 2.3.0                    # 指定版本号
#   ./build.sh patch --dry-run          # 只看动作不打 tar
#   ./build.sh patch --message "fix..." # 指定 CHANGELOG
#
# 流程:
#   1. 检查 git 状态干净
#   2. 脱敏 sanity check（敏感串扫描，失败拒绝打包）
#   3. 准备 build/ 目录
#   4. 复制 skill/ + runtime/ + extensions/ (排除 pyc/.v* 历史)
#   5. 自动生成 CHANGELOG.md (汇总 git log)
#   6. tar.gz 打包到 skill/release/
#   7. 打印发布命令
#
# 不会自动 publish — 发布是手动 `clawhub publish` 确认动作

set -euo pipefail

# ─── 路径 ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$SCRIPT_DIR"
PROJECT_ROOT="$(dirname "$SKILL_ROOT")"
RUNTIME_ROOT="$PROJECT_ROOT/runtime"
EXTENSIONS_ROOT="$PROJECT_ROOT/extensions"
BUILD_DIR="$SKILL_ROOT/build"
RELEASE_DIR="$SKILL_ROOT/release"
VERSION_FILE="$SKILL_ROOT/VERSION"

# ─── 参数解析 ────────────────────────────────────────────────
DRY_RUN=false
CHANGELOG_MSG=""
BUMP="${1:-patch}"

# 解析剩余参数
shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --message|-m) CHANGELOG_MSG="$2"; shift 2 ;;
    *) echo "❌ 未知参数: $1"; exit 1 ;;
  esac
done

# ─── 检查 git 状态 ──────────────────────────────────────────
if ! git -C "$PROJECT_ROOT" diff --quiet HEAD 2>/dev/null; then
  echo "❌ git dirty. commit 后再 build"
  exit 1
fi

# ─── 解析版本号 ─────────────────────────────────────────────
CURRENT="$(cat "$VERSION_FILE" 2>/dev/null || echo "2.0.0")"

IFS='.' read -ra V <<< "$CURRENT"
MAJOR="${V[0]:-0}"
MINOR="${V[1]:-0}"
PATCH="${V[2]:-0}"

case "$BUMP" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
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
echo ""

# ─── 脱敏 sanity check ──────────────────────────────────────
# 扫描 build 源区域，禁止敏感串进 tarball
SENSITIVE_PATTERNS=(
  "q2lrLIvUs"               # 旧 WiFi 密码（脱敏前的真实值）
  "Asur737"                 # 旧 WiFi SSID（脱敏前的真实值）
  "ghp_trNbh3"              # 旧 GitHub token 前缀（脱敏前的真实值）
)
# 注：YOUR_WIFI_PASSWORD / YOUR_WIFI_SSID / YOUR_SERVER_IP 是占位符（开源模板标准做法），
#     它们出现是预期的，不扫描。

echo "🔍 脱敏 sanity check..."
# 扫描源区域：runtime/ + extensions/ （skill/ 是元数据/build 工具自己，patterns 在那里出现是预期的）
SCAN_DIRS=("$RUNTIME_ROOT" "$EXTENSIONS_ROOT")
LEAKED=0
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
  matches=$(grep -rEln "$pattern" "${SCAN_DIRS[@]}" 2>/dev/null \
    --include="*.md" --include="*.py" --include="*.js" --include="*.ino" \
    --include="*.yaml" --include="*.yml" --include="*.json" \
    --include="*.txt" --include="*.sh" \
    --exclude-dir=build --exclude-dir=release --exclude-dir=__pycache__ \
    --exclude-dir=.git --exclude-dir=node_modules || true)
  if [[ -n "$matches" ]]; then
    echo "  ❌ 发现敏感串 '$pattern' 在："
    echo "$matches" | sed 's/^/    /'
    LEAKED=1
  fi
done

if [[ $LEAKED -eq 1 ]]; then
  echo ""
  echo "❌ 脱敏检查失败，先修复再 build"
  exit 1
fi
echo "  ✅ 无敏感串"
echo ""

# ─── 准备 build/ ────────────────────────────────────────────
echo "📂 准备 build/ ..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# ─── Step 1: 复制 skill/ 顶层文件 ─────────────────────────────
for f in SKILL.md README.md LICENSE agent-handler.js VERSION CHANGELOG.md; do
  if [ -e "$SKILL_ROOT/$f" ]; then
    cp -r "$SKILL_ROOT/$f" "$BUILD_DIR/"
  fi
done

# skill/scripts/ (handler 脚本)
if [ -d "$SKILL_ROOT/scripts" ]; then
  cp -r "$SKILL_ROOT/scripts" "$BUILD_DIR/scripts"
  # 清理 pyc
  find "$BUILD_DIR/scripts" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
  find "$BUILD_DIR/scripts" -name "*.pyc" -delete 2>/dev/null || true
fi

# ─── Step 2: 复制 runtime/ (核心产品代码) ─────────────────────
RT_BUILD="$BUILD_DIR/runtime"
mkdir -p "$RT_BUILD/data"

for f in cli.py db.py pipeline.py llm_config.py __init__.py config.yaml.example; do
  if [ -f "$RUNTIME_ROOT/$f" ]; then
    cp "$RUNTIME_ROOT/$f" "$RT_BUILD/$f"
  fi
done

# data/ 占位（生产 db 不打包）
touch "$RT_BUILD/data/.gitkeep"

# 清理 runtime pyc
find "$RT_BUILD" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$RT_BUILD" -name "*.pyc" -delete 2>/dev/null || true

# ─── Step 3: 复制 extensions/ ────────────────────────────────
# 复制全部 extensions，但排除：
#   - __pycache__/
#   - *.v1, *.v2, *.v3, *.v4, *.v*_partial 等历史备份
#   - code/data/*.json 里的运行时数据（保留 README）
#   - 内部 dev 笔记（kanban / notes / CHECKLIST / docs/plan / verify / roadmap / CHANGELOG）
if [ -d "$EXTENSIONS_ROOT" ]; then
  echo "📦 打包 extensions/ ..."
  rsync -a --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='*.ino.v*' \
            --exclude='*.ino.*_partial' \
            --exclude='code/data/*.json' \
            --exclude='code/server/server_v*.py' \
            --exclude='kanban.md' \
            --exclude='notes.md' \
            --exclude='CHECKLIST.md' \
            --exclude='docs/plan.md' \
            --exclude='docs/verify.md' \
            --exclude='docs/roadmap.md' \
            --exclude='docs/CHANGELOG.md' \
            "$EXTENSIONS_ROOT/" "$BUILD_DIR/extensions/"
fi

# ─── Step 4: 写 VERSION ─────────────────────────────────────
echo "$NEW_VERSION" > "$BUILD_DIR/VERSION"
echo "$NEW_VERSION" > "$SKILL_ROOT/VERSION"

# 同步 SKILL.md frontmatter 里的 version 字段
if [ -f "$BUILD_DIR/SKILL.md" ]; then
  sed -i "s/^version: .*/version: $NEW_VERSION/" "$BUILD_DIR/SKILL.md"
fi

# ─── Step 5: 生成 CHANGELOG.md ──────────────────────────────
CHANGELOG="$BUILD_DIR/CHANGELOG.md"
echo "📝 生成 CHANGELOG.md ..."

# 如果有指定 --message，用单行 summary
if [[ -n "$CHANGELOG_MSG" ]]; then
  CHANGELOG_BODY="$CHANGELOG_MSG"
else
  # 自动汇总：从上一个 VERSION tag（或首次 build 的最远 commit）到 HEAD
  # 用 git log 收集 commits
  LAST_TAG=$(git -C "$PROJECT_ROOT" describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$LAST_TAG" ]]; then
    RANGE="$LAST_TAG..HEAD"
  else
    RANGE="HEAD~20..HEAD"  # 没 tag 就取最近 20 个
  fi

  CHANGELOG_BODY=$(git -C "$PROJECT_ROOT" log --oneline --no-decorate $RANGE 2>/dev/null \
    | sed 's/^/  - /' \
    | head -50 || true)

  if [[ -z "$CHANGELOG_BODY" ]]; then
    CHANGELOG_BODY="  - (无 git log)"
  fi
fi

cat > "$CHANGELOG" <<EOF
# kids-points-v2 Changelog

All notable changes to this project will be documented in this file.

## v$NEW_VERSION ($(date +%Y-%m-%d))

$CHANGELOG_BODY

EOF

# ─── Step 6: tar.gz 打包 ────────────────────────────────────
TARBALL="$RELEASE_DIR/kids-points-v2-$NEW_VERSION.tar.gz"
mkdir -p "$RELEASE_DIR"

if [[ "$DRY_RUN" == "true" ]]; then
  echo ""
  echo "🔍 DRY RUN — 不实际打包"
  echo "   build/ contents:"
  find "$BUILD_DIR" -type f | sort | sed 's/^/    /'
  echo ""
  echo "   计划输出: $TARBALL"
  exit 0
fi

cd "$BUILD_DIR"
tar -czf "$TARBALL" .
cd "$SKILL_ROOT"

# ─── 摘要 ────────────────────────────────────────────────────
echo ""
echo "✅ Build 完成"
echo "   版本:     $NEW_VERSION"
echo "   tarball:  $TARBALL"
echo "   大小:     $(du -h "$TARBALL" | cut -f1)"
echo ""
echo "tarball 文件清单（前 30 行）："
tar -tzf "$TARBALL" | head -30
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "下一步: 发布到 ClawHub"
echo ""
echo "  clawhub publish $BUILD_DIR \\"
echo "    --slug kids-points-v2 \\"
echo "    --version $NEW_VERSION \\"
echo "    --changelog \"\$(cat $CHANGELOG | tail -n +5)\" \\"
echo "    --tags \"latest,kids,family,feishu,sqlite,llm\""
echo ""
echo "或者用 clawhub sync 扫描并发布（推荐）："
echo ""
echo "  cd $PROJECT_ROOT && clawhub sync"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"