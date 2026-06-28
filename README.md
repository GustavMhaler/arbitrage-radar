# 机会发现雷达 v2 (Arbitrage Radar)

> "选轻资产低成本,可重试,输了不痛不痒还能涨经验。" —— 原作者 #1

一个 Hermes Agent skill,用 **4 原则 + 6 维打分卡**评估副业/兼职/转型方向,输出打过分的候选清单。

**只做机会评估**,不做股票/币种推荐,不做代码生成,不做灰产。

---

## 它是干嘛的

你问"有什么副业可做",它不直接告诉你答案——而是给你一套**判断框架**:

- **4 原则**: 轻资产 + 信息差 + 跨市场 + 反消费
- **6 维打分卡**: 试错成本 / 经验可回收 / 中间商 / 跨市场加成 / 新兴市场 / 可 IP 化
- **7 条错误模式**: 命中任何一条直接 PASS
- **3 类应用模式**: 技能可复用 / 跨地区价差 / AI 杠杆

方法论提炼自某匿名知乎高赞作者的轻资产套利框架(2022-2025)。

---

## 什么时候用它

适合的提问:

- "我手里有 X 万,想搞副业,做什么好?"
- "学什么技能能变现?"
- "有什么跨市场套利的机会?"
- "如何用信息差赚钱?"
- "我能不能做 XX 这个生意?"
- "现在 2026 还有什么风口?"
- "换跑道,我想从 A 转到 B,你看行不行?"

不适用的提问(不会触发):

- "这个股票能不能买?"
- "帮我写代码"
- "翻译一下"
- "写个商业计划书"

---

## 一键安装(给 agent 发指令)

如果你已经装了 Hermes Agent,直接**复制下面这段,粘到和 agent 的对话里发出去**:

```
帮我安装这个 Hermes skill：https://github.com/GustavMhaler/arbitrage-radar.git
要求：
1. 用 git clone 到 ~/.hermes/skills/arbitrage-radar 目录(目录名必须等于 arbitrage-radar)
2. 装完后跑一下 hermes skills list 验证 skill 已被识别
3. 如果目录已存在,先备份再装
4. 装完告诉我怎么触发它
```

agent 会自己跑命令、装好、告诉你怎么用。**不需要你碰终端**。

### 命令行安装(给懂行的人)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/GustavMhaler/arbitrage-radar/master/install.sh)
```

或手动:

```bash
git clone https://github.com/GustavMhaler/arbitrage-radar.git ~/.hermes/skills/arbitrage-radar
```

装完后重启 Hermes(hermes gateway restart / 重启客户端 / 重新打开终端)。

---

## 触发指令

装好后,在 Hermes 里说任意一句:

- "帮我看看有什么副业可做"
- "扫描机会雷达"
- "我手里有 5 万,想搞副业"
- "2026 还有什么风口"
- "我想从程序员转行做产品经理,行不行?"

agent 会加载 skill,问你的画像(本金/技能/风险/时间/地理),然后按 4 原则 + 6 维打分卡给你 3-5 个打过分的候选。

---

## 它**不**会做的事

- ❌ 不推荐具体股票/币种/平台
- ❌ 不写代码 / 写商业计划书 / 写合同
- ❌ 不推荐灰产(色情/赌博/盗版/翻墙工具/撸毛)
- ❌ 不预判行情涨跌
- ❌ 不承诺收益(任何收益预期都基于同类案例的实测,不是承诺)

**边缘机会**(如:跨境电商/海外注册/AI 应用)会**明确标注"需自评合规"**,你得自己判断。

---

## 文件结构

```
arbitrage-radar/
├── README.md                ← 你正在读
├── install.sh               ← 一键安装脚本
├── SKILL.md                 ← agent 加载的主入口
├── agents/
│   └── openai.yaml          ← UI 元数据
└── references/
    ├── 01-principles.md         ← 4 条原则 + 金句
    ├── 02-opportunity-framework.md  ← 6 维打分卡
    ├── 03-application-patterns.md   ← 3 类应用模式
    ├── 04-red-flags.md          ← 7 条错误模式
    ├── 05-output-template.md    ← 输出骨架
    └── 99-source-index.md       ← 原文出处索引
```

---

## 怎么自己改这个 skill

V2 的设计遵循 [OpenAI skill-creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md) 方法论:

- `SKILL.md` 是给 agent 看的入口(< 500 行)
- `references/` 按主题拆分,按需加载
- `agents/openai.yaml` 是 UI 元数据

如果你想调整判断框架,改 `SKILL.md` 第 "4 原则" 和 "6 维打分卡" 章节。如果想调整详细评分标准,改 `references/02-opportunity-framework.md`。

---

## 更新日志

- **v2.0.0 (2026-06-28)**: 推倒重写
  - 移除所有灰产调性(加密/翻墙/色情/撸毛等)
  - 框架忠实于原作者提炼的 4 条原则
  - 走 skill-creator 推荐结构,SKILL.md < 500 行,详细内容 references/
  - 全部候选必须**明确标注"合规状态"**
  - 引用方式改为"匿名知乎高赞作者",不暴露个人
- **v1.x (已废弃)**: 因调性问题被多个 agent guardrail 拒绝触发,作废

---

## License

MIT。本仓库不复制原作者原文,只引用 #编号 + 主题。

---

**这个 skill 不收集任何数据、不联网(除非你让它搜公开信息)、不读你机器上的任何文件**。源码公开可审计。