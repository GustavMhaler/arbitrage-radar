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

# 4.5. 装 ddgs(Step 2.5 事实核查的 3 层 fallback 第 2 层,免费 DuckDuckGo,无需 API key)
echo
echo "[+] 检查 ddgs Python 包(ddgs DuckDuckGo 搜索,Step 2.5 fallback 用)"
if python3 -c "import ddgs" 2>/dev/null; then
  echo "    ddgs 已装,跳过"
else
  echo "    装 ddgs..."
  # Ubuntu/Debian 22.04+ 默认禁止 system pip,加 --break-system-packages
  if pip install --user --break-system-packages ddgs 2>/dev/null; then
    echo "    [OK] ddgs 装好"
  else
    echo "    [!] ddgs 装失败 — 不影响使用,只是 Tavily 不可用时降级会失败"
    echo "        手动: pip install --user --break-system-packages ddgs"
  fi
fi

# 4.6. 脚本加可执行位(有些 clone 不会保留 +x)
chmod +x "$TARGET/scripts/web_search.py" 2>/dev/null || true

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
  echo
  echo "  Step 2.5 事实核查(可选):装 ddgs 后脚本有 3 层 fallback,无需 API key 也能搜"
  echo "  测一下:python3 $TARGET/scripts/web_search.py 'test query' --num 2"
else
  echo
  echo "[X] 安装似乎有问题,$TARGET/SKILL.md 缺失或格式不对"
  exit 1
fi