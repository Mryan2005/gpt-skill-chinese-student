---
name: study-politics
description: Use as the politics domain model for source-faithful political concepts, principles, canonical expressions, comparisons, confusions, timelines, policy frameworks, and exam-oriented question mappings. learn remains the workflow front door.
---

# 政治领域模型

study-politics 定义政治知识应该如何表示和理解。它不是第二个 learn，也不是学习任务 Router。learn 选择 playbook 后，在政治 Subject 中加载本 skill 的 derived model。

## Non-negotiables

- Source 内容与 Derived 内容是不同实体。派生内容不得修改、覆盖或重写原文。
- 每个 Derived record 必须通过 sourceRefs 和 locator 追溯到原始材料。
- 教材原话、canonical wording、AI 提取、解释、易混点和题目推导必须分开。
- 原文措辞中的唯一、根本、本质、首要、核心、基础、前提、决定、体现等词不能被无证据替换。
- 派生卡可以删除、重建和重新组织；Source version 不因此改变。
- 政治卡片必须使用本领域 Card Type，不把数学 Card Schema 或通用四区块强行套用。

## Card Types

政治至少支持：

~~~text
concept
principle
canonical-expression
comparison
confusion
timeline
policy-framework
problem-pattern
~~~

字段和示例见 [politics-cards.md](references/politics-cards.md)。完整性与 Source/Derived 冲突见 [politics-integrity.md](references/politics-integrity.md)。平台不可变原则见 [platform-contract.md](../../references/platform-contract.md)。

## learn integration

learn 负责 ingest、topic study、question organization、Subject update、repair 和 readiness。study-politics 只负责政治派生内容的 Card Type、措辞保真、关系语义、题目映射和政治专项 readiness 解释。
