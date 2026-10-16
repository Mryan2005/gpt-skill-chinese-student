---
name: study-math
description: Use as the mathematics learning front door for systematic topic study, structured question sets, knowledge-map repair, formula-preserving records, and exam-readiness checks. Use learn for ordinary cross-subject learning, including small math requests.
---

# 中式学生：数学学习入口

study-math 是数学学习的 Front Door。它根据用户目标选择 playbook，再加载需要的数学合同、代理和 executable gate。用户只需要描述目标，不需要编排代理和校验步骤。

## Non-negotiables

- 一张卡只解决一个可以独立主动回忆的数学问题。
- 章节、目录和总览属于 module/metadata，不自动成为 question 或巨型复习卡。
- 数学内容不可静默猜测、补写或丢失。不可读内容必须保留边界。
- Source、Question、Card、Relation 分层保存。完整题目只存一份。
- 每道题恰好一个 primary card，其他知识点只能作为 secondary tags。
- Relation 必须有类型、方向和 why。Bridge 必须有真实出边。
- sourceStatus、questionStatus、solutionStatus、answerStatus 分开保存。
- 最终输出必须验证真实 artifact，不能只验证文件存在或提示词通过。

完整原则见 [principles.md](references/principles.md)；平台 Source/Derived Contract 见 [platform-contract.md](../../references/platform-contract.md)。不要把这些原则扩写回入口文件。

## Routing

| 用户目标 | Playbook |
| --- | --- |
| 新图片、PDF、教材或笔记进入数学记录 | [ingest-material.md](playbooks/ingest-material.md) |
| 系统学习一个章节或主题 | [learn-topic.md](playbooks/learn-topic.md) |
| 整理一组数学习题 | [organize-question-set.md](playbooks/organize-question-set.md) |
| 从结构化记录构建数学卡和关系 | [build-cards.md](playbooks/build-cards.md) |
| 向已有学科加入新材料 | [update-subject.md](playbooks/update-subject.md) |
| 修复已有数学知识网的结构问题 | [repair-knowledge-map.md](playbooks/repair-knowledge-map.md) |
| 检查是否可以用于考试 | [validate-exam-readiness.md](playbooks/validate-exam-readiness.md) |

如果目标跨越多个阶段，选择用户目标对应的主 playbook，并由它组合其他 playbook。不要要求用户重复描述内部执行仪式。

## Shared contract

1. 读取目标项目的 AGENTS.md、.codex/task-state.md、learner_state.md 和 design_memory.md（存在时）。
2. 使用同一份 Structured Math Records：modules、cards、questions、relations、sources、progress。
3. 代理只能写隔离报告。主 skill 是 canonical Markdown、知识网络 HTML、learner_state 和 task-state 的唯一合并者。
4. 数学记录最终投影到统一学科的 canonical Markdown、知识网络 HTML 和 learner_state。不得创建第二份数学真相。
5. 只在当前 playbook 需要时读取 references/card-schema.md、question-schema.md、relation-schema.md、source-schema.md、math-integrity.md、math-rendering.md 或 math-agents.md。

## Done gate

运行与当前 playbook 相关的校验器：

~~~text
validate_math.py
validate_math_cards.py
validate_markup.py
~~~

检查 source classification、Card Atomicity、题目完整性、primary mapping、公式完整性、答案证据、typed relations、实际 Markdown/HTML 输出和独立的知识/题目掌握度。任一核心 Gate 失败时报告 学习未完成，并把具体缺口传给 exam 的 图谱缺口。只有真实 artifact 和所有必要 Gate 都通过时，才能报告 可用于考试。
