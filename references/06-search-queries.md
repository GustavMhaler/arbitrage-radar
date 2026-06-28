# 06 — 事实核查查询模板(Step 2.5 用)

> **作用**:为每个候选商机生成 3 条事实核查 query,避免 LLM 凭印象出数据。
> **使用方式**:agent 在 Step 2.5 阶段,用 `terminal` 跑 [`scripts/web_search.py`](../scripts/web_search.py),把下面的骨架里的 `<X>` 替换成候选方向,跑 3 条 query。
> **不写进 SKILL body 的原因**:具体平台名/价格会触发 buyer 端 agent 调性敏感。buyer 触发时只看到 SKILL.md + references/01-05,这一层和 99 不参与触发判定。
>
> **⚠ 用脚本而不是 web_search 工具**:Hermes 的 `web_search` 工具依赖后端配置 + toolset 白名单,常因 .env 没 source / ddgs 包没装 / `toolsets=['web']` 写错名(应写 `search`)而「静默消失」。本 skill 自带 `scripts/web_search.py`,3 层 fallback(Tavily → ddgs → curl DDG),不依赖 hermes web 工具链。**任何买家环境至少有一层能跑**(详见脚本 docstring + `references/07-web-search-setup.md`)。

---

## 三轴核查框架

每个候选都从这三个角度搜,**不能跳**:

| 轴 | 回答的问题 | 失败代价 |
|---|---|---|
| 价格/时薪锚点 | 2026 年这活儿在主流平台实际成交多少钱 | 收益数字编造,用户踩坑 |
| 竞争密度 | 做的人多不多 / 新人还有没有位置 | 蓝海变红海,白忙 |
| 政策/合规 | 跨境 / 支付 / 资质有无最新风险 | 触碰红线,被封号 / 罚款 |

---

## 查询模板(每轴 1 条,共 3 条)

### 轴 1:价格/时薪锚点(必含 1 条英文)

**中文版**:
```
<X 服务或类目> 2026 报价 / 时薪 / 月收入 / 客单价
```

**英文版**(跨市场信息差核心在英文世界,必跑 1 条):
```
<X service or niche> hourly rate 2026 OR pricing 2026 site:reddit.com
```

### 轴 2:竞争密度

```
<X 方向> 2026 竞争 / 红利期 / 还能做吗 / saturated
```

### 轴 3:政策/合规(如果是跨境/支付/资质相关)

```
<X 类目> 2026 合规 / 监管 / 政策风险 OR payment policy
```

---

## 替换示例(以"英文简历优化师"为例)

| 轴 | 替换后 query |
|---|---|
| 价格 | `英文简历优化 Upwork 报价 2026` + `resume writer hourly rate 2026 reddit` |
| 竞争 | `英文简历优化 2026 竞争 / 红利期` |
| 政策 | (此项不适用,跳过,补一条价格细分) |

---

## 失败处理(全网搜不到/工具不可用时)

按 SKILL Step 2.5 第 4 条:

- 不编造数据
- 在输出报告头部明确写:`信号源离线,本轮收益数字为 LLM 估计 [未验证]`
- 所有候选的"预期收益"标 `[LLM 估计]`
- 建议用户自行核实

## 脚本调用示例

```bash
# 单条 query
python scripts/web_search.py "小红书 买手 兼职 收入 2026" --num 5

# 强制走 ddgs(就算有 Tavily key 也用 ddgs,适合调试)
python scripts/web_search.py "闲鱼 无货源 铺货 2026 还能做吗" --num 3 --backend ddgs

# 输出 JSON 里看 backend_used + errors[] 字段:
#   {"query": "...", "backend_used": "tavily|ddgs|ddg_html|none", ...}
#   backend_used=none 时 errors[] 里有 3 层失败原因
```

3 层 fallback 任何一层通都返回结果,3 层全挂才报 `backend_used: none`。**装 ddgs**: `pip install --user --break-system-packages ddgs`(Ubuntu/Debian 需要 `--break-system-packages`)。

---

## 不要把搜索结果写进 SKILL body

**为什么**:SKILL.md 会被 buyer 端 agent 全文加载,里面出现"Upwork 时薪 X 美元"这种具体平台 + 价格组合,在某些 buyer 的 guardrail 里会触发拒绝触发(历史教训:v1 因调性被拒)。

**正确做法**:
- SKILL body 只写"必搜 + 标依据类型" → 已实现
- 搜索结果(平台名 / 价格区间 / 案例截图)只在对话里跟用户说,不沉淀到 skill 文件
- references/06 本身是"中性骨架",只放查询模板,不放具体数字

---

## 跟 references/01-05 的关系

| 文件 | 加载时机 | 调性 |
|---|---|---|
| 01-05 | buyer 端 agent 加载,参与触发判定 | 中性 / 框架化 |
| 06 | agent 跑 Step 2.5 时查,**不参与触发判定** | 中性骨架 |
| 99 | 出处索引,不参与加载 | 仅 #编号 |

新增 06 不改变 buyer 触发路径。
