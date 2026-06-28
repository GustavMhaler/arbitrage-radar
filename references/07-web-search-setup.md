# web_search 工具配置与降级(2026-06-28 踩坑沉淀)

> 本文件是 Step 2.5 的工程支撑。SKILL.md 描述「必做」,这里回答「不可用时怎么 debug + 降级」。

## 1. 为什么「web_search 不存在」是常见误判

Hermes Agent 的 `web_search` / `web_extract` 是**后端路由型**工具 —— 工具本身不内置搜索引擎,而是按 `~/.hermes/config.yaml` 的 `web.backend` 配置转发到某个提供商。**后端没配 → 工具不出现在 tool 列表里**,agent 调时返回 `Tool 'web_search' does not exist`。

8 个支持的后端(按门槛排序):
| 后端 | 成本 | 注册 | 适合 |
|---|---|---|---|
| `ddgs` | 免费 | 无需 | **默认兜底**,DuckDuckGo 抓取 |
| `searxng` | 免费 | 自托管 Docker | 隐私党,自部署 |
| `brave-free` | 免费 | brave.com/search/api | 国内通,需注册 |
| `firecrawl` | 付费 | firecrawl.dev | 提取+搜索 |
| `tavily` | 付费 | tavily.com | 1000 次/月免费额度 |
| `exa` | 付费 | exa.ai | 1000 次/月免费额度,语义搜索 |
| `parallel` | 付费 | parallel.ai | AI 深度研究 |
| `xai` | 付费 | x.ai Grok API | LLM 选 URL(有 prompt injection 风险) |

## 2. 30 秒诊断脚本

```bash
# 1. 工具是否存在于 tool 列表
hermes config show | grep -A 3 web

# 2. 当前后端是什么(应该看到 backend 字段,空就是没配)
grep -A 2 "^web:" ~/.hermes/config.yaml

# 3. 立刻开 ddgs 兜底
hermes config set web.backend ddgs

# 4. 重启 session 后再调 web_search
```

## 3. 走 delegate_task 的正确姿势

子 agent 默认继承 parent 的 toolset 裁剪,**所以 parent 没 web_search,子 agent 也没有**。

**正确写法(2026-06-28 踩坑实证)**:
```python
delegate_task(
  goal="跑 4 条 search query,走 scripts/web_search.py ...",
  toolsets=['search']   # ← 是 'search' 不是 'web'
)
```

⚠️ **坑**:hermes-agent skill 文档示例写的是 `toolsets=['web']`,实测在部分 session 里 web_search 不出现。**改成 `['search']` 后稳定通过**(可参考 hermes-agent skill troubleshooting 的 "verified 2026-06-28" 段)。

子 agent 第一次报「没有 web_search」?几乎 100% 是父 agent 的后端没配或 toolset 名写错,**不是子 agent 工具链坏了**。

**最稳的姿势:不要让子 agent 调 web_search,直接让它 `terminal` 跑 [`../scripts/web_search.py`](../scripts/web_search.py)**。脚本内含 3 层 fallback(Tavily HTTP API → ddgs Python 包 → curl DDG HTML),不依赖任何 hermes web 工具链。SKILL.md Step 2.5 已经规定走这个脚本。

## 4. web_search 仍不可用时的降级方案

按 skill 规则「搜不到时标 `[未验证]`,不编造数据」,但用户可能想跑。**首选**:`terminal` 跑 [`../scripts/web_search.py`](../scripts/web_search.py),它已经内含 3 层 fallback,任何环境至少有一层能跑。**次选**:

- **方案 A(自验)**: 平台直接看。Fiverr/小红书/闲鱼本身就有公开数据,用户 15 分钟自己看,比任何搜索都准
- **方案 B(走 curl + 公共 SearXNG 实例)**: `curl -s "https://searx.be/search?q=xxx&format=json" | jq` —— 有时效性 + 易被反爬
- **方案 C(走 Firecrawl 单次抓取)**: 用户提供 FIRECRAWL_API_KEY,直接抓 4 个目标 URL
- **方案 D(本地 LLM 锚点 + 用户核验)**: agent 基于行业常识给锚点值,**明确标 `[未验证,需用户核验]`**,用户用方案 A 自己核对

**禁止的降级**:
- ❌ LLM 凭印象写具体数字(2026 年 X 元/月)然后不标 `[未验证]`
- ❌ 拿「2022 年知乎高赞答案」当 2026 年事实用
- ❌ 直接说「搜不到,没法做」然后放弃(违反 skill 「哪怕只搜到 1 条也有意义」)

## 5. 官方文档 URL(必查,不靠记忆)

- 中文: https://hermes-agent.nousresearch.com/docs/zh-Hans/user-guide/features/web-search
- 英文: https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search

文档覆盖 8 个后端配置、per-capability 配置、自动检测链、故障排查(`web_search` 返回 success=false / `web_extract` 提示 search-only / SearXNG 0 结果等 5 个常见 case)。

## 6. 教训沉淀(给 agent 自己看)

- **「工具不存在」永远先查文档,不要先下结论**。用户记忆里 agent 第二次硬说「没这个工具」是非常负向的体验
- **「tool list 里没看到」 ≠ 「没装」**。默认 toolset 按后端裁剪,后端没配就裁掉了
- **子 agent 报「没 web_search」时,先怀疑父 agent 配置,不要怀疑子 agent 工具链**
- **agent 固执地连续两次说「没工具」,根本原因是「没翻文档」**。以后任何「工具不可用」类报错,**第一步必须 curl 官方文档**,5 分钟能解决很多假性故障

## 7. 2026-06-28 实证补丁(给「这个文档自己也错了」埋个账)

本文件上一版第 3 节说 `toolsets=['web']` 是「正确写法」,**实测在 ddgs 后端下不可靠**(子 agent 报 `Tool 'web_search' is not available in this environment`)。修订:

- 改为 `toolsets=['search']` 稳定通过(详见第 3 节)
- 终极方案:**永远不要让子 agent 调 web_search 工具**,统一走 `scripts/web_search.py`(`terminal` 调,3 层 fallback,完全脱离 hermes web 工具链)
- 不要相信 hermes-agent skill 文档里 `toolsets=['web']` 的示例 — 至少在 ddgs 后端下不对
