# 数学专项共用规则

平台 Source/Derived Contract 见 [platform-contract.md](../../references/platform-contract.md)。

## 平台边界

`learn` 是跨学科学习基础设施：它统一来源、证据、canonical Markdown、知识网络 HTML、搜索、进度和持久化状态。`study-math` 只提供数学领域的拆分、卡片、题库、关系、公式和考试可用性模型。

数学的结构化记录可以作为中间层保存，但必须投影到同一学科的 canonical Markdown、唯一知识网络 HTML 和统一 `learner_state`。不要让 `learn` 与 `study-math` 各自产生一份数学真相。

## 证据状态

每条重要内容明确标记下列一种或多种来源边界：

- `原始材料`：用户提供的教材、图片、试卷或原始笔记中可读的内容；
- `外部补充`：学习阶段为理解概念而查到的解释或标准公式；
- `题目推导`：根据题干和可验证步骤得到的推导；
- `官方解析可读部分`：提供的答案/解析材料中实际可读的部分；
- `待核实`：无法从现有来源确认的内容。

不同证据状态不能静默合并。外部补充不能覆盖原始题面，历史答案不能冒充官方答案，截断解析不能包装成完整解析。

## 状态分离

数学记录至少分开：

```text
sourceStatus
questionStatus
solutionStatus
answerStatus
```

例如 `questionStatus = COMPLETE` 与 `solutionStatus = SOLUTION_INCOMPLETE` 可以同时成立。不要用一个 `status` 隐藏不同缺口。

## 稳定 ID 与所有权

- module、card、question、relation、source、mathObject 都有稳定唯一 ID；
- Question Bank 拥有完整题干，Card 只保存 Question ID；
- Source 拥有来源位置和 provenance；
- Relation 拥有语义方向和 why；
- Markdown/HTML 是面向人的投影，不承担唯一数据库职责。

## 推荐校验顺序

```text
Source Classification
→ Structured Records
→ validate_math.py
→ validate_math_cards.py
→ canonical Markdown
→ validate_markup.py
→ HTML/MathJax/KaTeX 实际渲染检查
→ exam-readiness
```

遇到失败先修复产生错误的结构化记录，再重新生成投影。不要在 HTML 渲染层用正则掩盖源数据错误。
