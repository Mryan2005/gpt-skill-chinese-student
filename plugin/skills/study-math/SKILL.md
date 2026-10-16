---
name: study-math
description: Use for systematic mathematics learning, exam-oriented math knowledge graphs, formula-preserving question banks, mathematical proofs or derivations, and math-specific card, relation, and readiness checks. The general learn skill remains the fallback for ordinary cross-subject learning, including small math requests.
---

# 中式学生：数学专项学习

`study-math` 是数学领域的认知模型，不是第二个学习插件，也不是把 `learn` 复制一遍再加数学 `if/else`。

## 职责边界

- `learn` 继续负责所有学科共用的来源、证据、canonical Markdown、知识网络 HTML、搜索、进度和持久化边界。普通的数学资料学习仍可直接使用 `learn`。
- `study-math` 在同一套平台能力之上规定数学应该如何拆分、回忆、解题、建关系、保存题目和判断考试可用性。
- 数学最终仍只有一份 canonical Markdown、一份学科知识网络 HTML 和一份统一的 `learner_state`。`math-records.json` 是结构化中间层，不是第二份数学真相。
- `exam` 仍只消费当前学科图谱；`check` 仍只读检查可达性。数学专项检查先验证结构化记录，再验证写回的统一图谱。

当请求只是“学习这几页数学教材”时，`learn` 可以独立完成；当请求明确涉及系统构建数学网络、大量数学习题、公式/证明、数学题型或考研数学复习时，使用本 skill。不要通过修改 `learn` 的描述把数学排除出去。

## 不可破坏的数学契约

1. 一张数学卡只解决一个可以独立主动回忆的数学问题。章节、目录和总览是 `module`/metadata，不自动成为复习卡。
2. Card、Question、Relation、Source 分层保存。完整题目只存一份，卡片只保存题目 ID。
3. 每道题恰好一个 `primaryCardId`；其他知识点只能进入 `secondaryCardIds`，并且必须有真实解题动作作为依据。
4. 公式是结构化数学对象，不是可以静默丢失的普通文本。无法核实的公式、选项、矩阵、上下限或图形必须进入不完整状态。
5. 关系必须有方向、类型和 `why`。Bridge 没有真实出边就是 `EMPTY_BRIDGE`。
6. `sourceStatus`、`questionStatus`、`solutionStatus`、`answerStatus` 分开记录。残缺题保留，不用章节总览顶替。
7. 知识掌握度和题目掌握度分开统计。做对一道题不能推导出掌握整个知识点。

## 工作流

### 0. 固定项目边界

读取目标项目的 `AGENTS.md`、`.codex/task-state.md`、`learner_state.md` 和 `design_memory.md`（存在时），确认原始资料、canonical 输出和当前图谱。任何来源、排除项、题号、映射或完成状态变化先写入任务状态。

### 1. Source Intake 与分类

逐份读取原始资料，按 [math-knowledge.md](references/math-knowledge.md) 的 `entityType` 分类。只有 `entityType = question` 的记录可以进入 Question Bank；章节标题、章节总览、题组说明、页眉页脚和知识列表只能是 metadata/evidence。不要先把总览放进 `examples`，再靠渲染正则过滤。

保留原始来源和不可读边界。公式、选项、图形、跨页题和分问都登记为 `mathObjects` 或带来源的题目片段；不能从外部网页猜回原题。

### 2. 生成 Structured Math Records

先生成同一份结构化记录：

```text
modules → cards → questions → relations → sources → progress
```

基础 JSON 形状见 [math-record.schema.json](schemas/math-record.schema.json)；跨记录语义和考试闸门由 `scripts/validate_math.py` 执行。

运行：

```text
python scripts/validate_math.py examples/math-records.json
python scripts/validate_math_cards.py examples/math-records.json
python scripts/validate_markup.py <canonical-markdown> <reports>
```

先修复结构错误，再生成 Markdown/HTML；不要把自由文本 Markdown 当作数据库，再从 Markdown 猜题目和关系。

### 3. 构建数学卡

使用 [math-cards.md](references/math-cards.md) 中的七种 Card Type：`definition`、`theorem`、`formula`、`method`、`problem-pattern`、`comparison`、`bridge`。每张卡必须有 `recallPrompt`、一个 `atomicity.coreQuestion`、类型专属内容、来源和可追踪的题目 ID。

完成 Card Atomicity/Size Gate：核心问题只能有一个；公式、步骤、易错点和精选题目超过边界时拆卡，不用字符数机械截断。章节层级放在 `modules`/`parentId`，语义关系放在 typed `relations`。

### 4. 结构化题库与映射

按 [math-questions.md](references/math-questions.md) 建立稳定 Question ID，保留原题号、题型、题干、选项、图形、分问、解析和答案证据。先根据真实解题动作写 `mappingEvidence.coreOperations`，再选一个 `primaryCardId`；不能由章节归属或已有挂载反推考点。

选择题、填空题和解答题的完整性检查不同。题面残缺、公式丢失、解析截断或答案来源不明时，保留记录并设置明确状态，不能用空白、章节摘要或历史答案伪装完成。

### 5. 关系与统一输出

按 [math-relations.md](references/math-relations.md) 创建有向关系，并为每条关系写解释。把结构化记录投影到当前学科的 canonical Markdown 和唯一知识网络 HTML；来源证据放在可折叠/次级区域，数学正文先回答“现在要记什么”。更新统一 `learner_state`，不要创建与 `learn` 竞争的数学学习状态。

### 6. Math Exam Readiness Gate

按照 [math-integrity.md](references/math-integrity.md) 和 [math-rendering.md](references/math-rendering.md) 完成题目、解析、答案、公式、关系、主动回忆和渲染检查。任一核心 Gate 失败都标记 `学习未完成`，把具体缺口带入 `exam` 的 `图谱缺口`；不能因为 HTML 能打开就报告可用于考试。

## 四角色数学学习代理

复杂批次读取 [math-agents.md](references/math-agents.md)，使用四份隔离报告：

1. 数学源材料提取：只提取文字、公式、题号、图形、版面和不可读边界；
2. 数学实体分类/题目结构化：分类 metadata/question，拆分 Question Record；
3. 数学解析与答案验证：检查解析完整性、答案来源和推导证据；
4. 数学知识卡与关系映射：选择 Card Type、primary card、secondary tags 和 typed relations。

代理只能写各自报告，主 skill 是 canonical Markdown、图谱、学习状态和任务状态的唯一写入者。每份报告都必须标记 `原始材料`、`外部补充`、`题目推导`、`官方解析可读部分` 或 `待核实`。

## 输出报告

完成时报告：职责边界、修改文件、七种 Card Type、Card/Question/Relation/Source schema、结构化记录路径、primary mapping、去重、Source Classification、Formula Integrity、Answer Evidence、Atomicity Gate、Math Exam Readiness Gate、validator/回归/兼容性结果。至少展示函数极限 Definition、Lagrange 定理 Theorem、比值判别法 Method、递推数列求极限 Problem Pattern、级数判别选择图 Bridge，以及一条完整 Question Record 的映射证据。
