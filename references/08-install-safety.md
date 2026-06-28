# 08 — install.sh 安全性 + 本地开发与 GitHub 仓库的同步陷阱

> 本文件是 skill 作者侧的工程笔记,不是 buyer 必读。给将来改这个 skill 的人(包括我自己)看。

## 1. install.sh 会无声覆盖你的本地改进

**踩坑记录(2026-06-28,verifying arbitrage-radar v2.1.1)**:

我在本地把 `SKILL.md` / `install.sh` / `references/06-07` / `scripts/web_search.py` 全改完了,跑了一次 `bash install.sh` 验流程,结果:
- install.sh 检测到 `~/.hermes/skills/arbitrage-radar/` 已存在,把它 mv 成 `.bak.<timestamp>`
- 然后从 GitHub clone 了一份**v2.0.0 的旧版**
- 我所有的 v2.1.x 改进都被覆盖了,只剩 .bak 目录里
- 06-search-queries.md / 07-web-search-setup.md / scripts/ 这三个新文件在 GitHub 仓库**根本不存在**

**结论**:
- `bash install.sh` **不是验证脚本**,是**生产环境的安装/升级命令**
- 它会无条件用 GitHub 仓库的最新 commit 覆盖 `~/.hermes/skills/arbitrage-radar/`
- 改本地后没 push,跑 install.sh 你的改动就丢了
- 改本地后**只 push 了部分文件**(比如只 push SKILL.md 没 push scripts/),跑 install.sh 会出现"SKILL.md 是新的但 scripts/ 是旧的"的不一致状态

## 2. 改 skill 的正确工作流

1. **改本地** —— 在 `~/.hermes/skills/arbitrage-radar/` 改文件
2. **本地端到端测试** —— `hermes` 加载 skill,触发核心流程,确认不报错
3. **完整 diff 一次** —— `cd ~/.hermes/skills/arbitrage-radar && git status --short` 看**所有**改动
4. **确认改动包含新增文件** —— `ls scripts/ references/` 对比 GitHub 仓库的 `https://github.com/GustavMhaler/arbitrage-radar`
5. **一次性 commit + push 所有改动** —— `git add -A && git commit -m "..." && git push`
6. **push 完成后才能跑 install.sh** —— 验证它真的从 GitHub clone 到了你刚才 push 的版本

## 3. install.sh 本身的改进(已加,2026-06-28)

- **自动装 ddgs**(Step 2.5 fallback 的第 2 层)。`pip install --user --break-system-packages ddgs`,失败不阻塞
- **脚本加可执行位** —— `chmod +x scripts/web_search.py`(git clone 有时不保留 +x)
- **给买家一行自测命令** —— `python3 $TARGET/scripts/web_search.py 'test query' --num 2`

## 4. 备份策略(已内置)

install.sh 检测到目标已存在时会**自动 mv 到 `${TARGET}.bak.<timestamp>`**,不会直接覆盖。这是 last-resort 安全网,但不替代**先 push 再跑 install.sh** 的纪律。

**恢复本地 v2.1.x 的命令**(如果你和我一样不小心跑过 install.sh 覆盖了):
```bash
ls ~/.hermes/skills/ | grep arbitrage-radar
# 找到 .bak.<timestamp> 目录,例如 .bak.1782649797
cp -r ~/.hermes/skills/arbitrage-radar.bak.<timestamp>/* ~/.hermes/skills/arbitrage-radar/
```

## 5. 跟 references/07 的关系

- `07-web-search-setup.md` —— buyer 侧 / agent 侧的 web 搜索可用性踩坑
- `08-install-safety.md`(本文件) —— 作者侧的 install.sh + 同步踩坑
- 两个文件不重叠,07 是 SKILL.md 跑不跑得起来,08 是作者改 skill 时怎么不丢自己的改动

## 6. 给未来 agent 的提醒

看到 `bash install.sh` 跑在已经存在的 skill 目录上 → 立刻意识到 "它会备份 + clone 新版覆盖",**先确认 GitHub 仓库反映了你想要的最新状态**,再跑。
