# 中式学生

chinese-student 是一个面向本地学习资料的 Agent Plugin。它把教材、图片、试卷和解析整理为可追溯的学科知识图谱，并保留足够的证据边界，供后续闭卷考试和考前检索使用。

本仓库包含插件源文件、数学专项学习模型、结构化记录 schema 和可重复运行的校验器。它不是某个具体学科的学习资料库，也不会把用户的原始图片或试卷上传到仓库。

插件提供方：Mryan2005。

## 核心 skills

| Skill | 用途 |
| --- | --- |
| learn | 通用学习流程。整理任意学科的来源、知识卡、关系、canonical Markdown 和知识网络 HTML。 |
| update | 插件版本迁移器。迁移旧 Subject 的 Derived、schema、artifact 和 progress，不修改 Source。 |
| relearn | 破坏性重建流程。确认后删除 Derived，保留 Source，再从头调用 learn 和领域模型。 |
| study-math | 数学专项流程。支持数学卡片类型、结构化题库、公式完整性、数学关系和考试可用性闸门。 |
| study-politics | 政治领域模型。保存教材原文与派生内容的 provenance，并支持概念、原理、标准表述、比较和易混点卡。 |
| exam | Assessment/Evaluation Runner。在冻结 Subject 上完成闭卷首轮、评分、错误分析和 Learning Gap Report。 |
| check | 独立的只读多代理 QA/Auditor。由来源、结构、内容、覆盖、题目、解法、数学、LaTeX、关系、provenance、渲染和检索审计代理并行检查，再由 Finding Merger 去重并定位根因。 |
| sort | 安全的复习优先级投影。按考试价值、风险、依赖、薄弱度和近期错误生成带理由的 review order，不修改知识内容或 canonical structure。 |

learn 是跨学科平台，不是“非数学 skill”。普通数学资料仍可使用 learn。当任务需要系统数学网络、大量数学习题、公式与证明、数学题型或考研数学复习时，使用 study-math。

learn 是整个插件的学习 Front Door。它先按用户目标选择材料摄入、主题学习、题目整理、Subject 更新、知识库修复或 readiness 检查，再按学科加载领域模型。study-math 负责数学认知结构，learn 负责学习工作流。

study-math 是一个数学学习 Front Door。它根据用户目标路由到材料摄入、主题学习、题组整理、卡片构建、主体更新、知识网修复或考试可用性检查 playbook。用户描述目标即可，不需要自己编排代理和校验步骤。

study-politics 是由 learn 加载的政治领域模型。它区分教材原文与 AI 派生内容，并定义政治专属的概念、原理、标准表述、比较、易混点、时间线、政策框架和题型卡。

check 不参与构建或修复。它读取统一 Subject 和领域 contract，先重置一次性
`.check/current` 工作区，再由隔离审计代理验证真实 artifact，最后报告 severity、
证据、根因和 repairOwner。代理只能写自己的临时报告；Finding Merger 只合并和
验证，不执行 repair。Agent thread 容量只改变并行度，不改变 required audit
范围；容量不足时 check 会分批、共享 worker，或由 orchestrator 顺序执行。

sort 不参与知识构建或正确性审计。它读取当前 artifact、领域重要性、learner_state、
exam gap 和 check findings，只写独立的 review-priority projection。canonical card
内容、章节树、关系和学习状态保持不变。

exam 直接读取原始试卷和解析 PDF。禁止 OCR、OCR 中间文本、外部 OCR 服务和委托 OCR；看不清的内容必须记录为不可读。

## 设计边界

learn 统一平台能力：

~~~text
Source / Provenance
Knowledge Graph
Question Bank 基础能力
Progress
Search
Canonical Markdown
HTML / Site 输出
通用学习状态
~~~

study-math 定义数学认知结构：

~~~text
数学卡片
数学知识层级
数学语义关系
数学题目与解题动作
公式和 MathObject 完整性
答案证据
主动回忆
Math Exam Readiness
~~~

两个 skill 写回同一学科的 canonical Markdown、知识网络 HTML 和 learner_state。study-math 的 math-records.json 是结构化中间层，不是第二份数学真相。

## 数学专项模型

study-math 支持七种 Card Type：

~~~text
definition
theorem
formula
method
problem-pattern
comparison
bridge
~~~

每张卡必须有一个 recallPrompt 和一个原子化的 atomicity.coreQuestion。章节总览属于 module/metadata，不会自动成为一张巨型复习卡。

Question Bank 与知识卡分离。每道题只有一个 primaryCardId，其他卡只能通过 secondaryCardIds 引用。题目、解析、答案和来源分别保存状态，公式丢失、解析截断和历史答案不会被静默包装成完整内容。

## 目录

~~~text
plugin/
├─ plugin.json
└─ skills/
   ├─ learn/
   │  ├─ SKILL.md
   │  ├─ playbooks/
   │  ├─ references/
   │  └─ scripts/
   ├─ update/
   │  ├─ SKILL.md
   │  ├─ migrations/
   │  ├─ playbooks/
   │  ├─ references/
   │  └─ scripts/
   ├─ relearn/
   │  ├─ SKILL.md
   │  ├─ examples/
   │  ├─ playbooks/
   │  ├─ references/
   │  └─ scripts/
   ├─ study-math/
   │  ├─ SKILL.md
   │  ├─ agents/openai.yaml
   │  ├─ playbooks/
   │  ├─ schemas/math-record.schema.json
   │  ├─ references/
   │  ├─ examples/math-records.json
   │  └─ scripts/
   ├─ study-politics/
   │  ├─ SKILL.md
   │  ├─ agents/openai.yaml
   │  └─ references/
   ├─ check/
   │  ├─ SKILL.md
   │  ├─ agents/
   │  ├─ playbooks/
   │  ├─ references/
   │  └─ scripts/
   ├─ sort/
   │  ├─ SKILL.md
   │  ├─ agents/openai.yaml
   │  ├─ playbooks/
   │  ├─ references/
   │  ├─ examples/
   │  └─ scripts/
   └─ exam/
      ├─ SKILL.md
      ├─ playbooks/
      ├─ references/
      └─ scripts/
tests/
└─ test_validate_math.py
~~~

## 本地验证

在仓库根目录运行：

~~~powershell
python -X utf8 plugin/skills/study-math/scripts/validate_math.py plugin/skills/study-math/examples/math-records.json

python -X utf8 plugin/skills/study-math/scripts/validate_math_cards.py plugin/skills/study-math/examples/math-records.json --require-type definition --require-type theorem --require-type formula --require-type method --require-type problem-pattern --require-type comparison --require-type bridge

python -X utf8 plugin/skills/study-math/scripts/validate_markup.py plugin/skills/study-math

python -X utf8 -m unittest discover -s tests -v
~~~

validate_math.py 检查结构化记录和数学考试闸门。validate_math_cards.py 聚焦 Card Atomicity、Card Size 和类型字段。validate_markup.py 检查 Markdown 数学定界符和裸 LaTeX 命令。实际 HTML 页面仍需在具体 Site 输出生成后检查公式、搜索、卡片点击和浏览器 console。

Playbook 只加载当前任务需要的 schema、完整性规则、渲染规则和代理分工。这样入口保持稳定，具体流程可以独立演进。

## 证据规则

学习内容必须区分：

~~~text
原始材料
外部补充
题目推导
官方解析可读部分
待核实
~~~

外部网页只能帮助理解定义、条件、证明或背景，不能偷偷修补原始题面，也不能把推导答案写成官方答案。源资料不完整时保留 Question Record，并设置明确的 questionStatus、solutionStatus 或 answerStatus。

## 贡献与授权

本仓库不是开放源码项目。未经版权所有者事先书面许可，不得复制、修改、分发、再许可、商业使用、训练模型或将本仓库内容打包到其他插件中。详见 LICENSE。

## 版权

Copyright (c) 2026 YAN ZHIZHONG. All rights reserved.
