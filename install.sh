#!/usr/bin/env bash
# 一键安装 arbitrage-radar skill (v2)
# 用法：bash install.sh
set -e

REPO_URL="https://github.com/GustavMhaler/arbitrage-radar.git"
SKILL_NAME="arbitrage-radar"
TARGET="$HOME/.hermes/skills/$SKILL_NAME"

echo "==> arbitrage-radar v2 一键安装"
echo

# 1. 检查 git
if ! command -v git >/dev/null 2>&1; then
  echo "[X] 找不到 git，请先安装 git"
  echo "    Ubuntu/Debian : sudo apt install git"
  echo "    macOS         : xcode-select --install"
  echo "    Windows       : https://git-scm.com/download/win"
  exit 1
fi

# 2. 检查 ~/.hermes/skills 目录
if [ ! -d "$HOME/.hermes" ]; then
  echo "[!] 找不到 ~/.hermes 目录，请先安装 Hermes Agent"
  echo "    安装地址：https://hermes-agent.nousresearch.com/docs"
  exit 1
fi
mkdir -p "$HOME/.hermes/skills"

# 3. 已存在则备份
if [ -d "$TARGET" ]; then
  BAK="${TARGET}.bak.$(date +%s)"
  echo "[!] $TARGET 已存在,备份到 $BAK"
  mv "$TARGET" "$BAK"
fi

# 4. clone
echo "[+] 从 $REPO_URL clone 到 $TARGET"
git clone "$REPO_URL" "$TARGET"

# 5. 验证
if [ -f "$TARGET/SKILL.md" ] && head -1 "$TARGET/SKILL.md" | grep -q "^---"; then
  echo
  echo "[OK] 安装成功"
  echo
  echo "  skill 已安装到: $TARGET"
  echo "  请重启 Hermes (hermes gateway restart 或重新打开客户端) 让它扫描新 skill"
  echo
  echo "  验证方法:在 Hermes 里说 '帮我扫一遍商机,有什么副业可做'"
  echo "  如果它开始调用 arbitrage-radar,说明装好了"
  echo
  echo "  或:运行 hermes skills list,确认 arbitrage-radar 在列表中"
else
  echo
  echo "[X] 安装似乎有问题,$TARGET/SKILL.md 缺失或格式不对"
  exit 1
fi