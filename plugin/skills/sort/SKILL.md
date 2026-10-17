---
name: sort
description: Use as the safe review-priority front door to rank existing knowledge cards by learning value and risk without changing canonical learning content or structure.
---

# 中式学生：复习排序入口

`sort` 只决定“现在先看什么”。它读取当前 Subject、领域 contract、`.local/learner`
中的 Error Model、Mastery、Observations、Explanation Model、exam gap 和 check findings，生成一个可解释的 review-priority projection。
它不判断知识是否正确，也不重写卡片或打乱课程结构。

## Non-negotiables

- 只写 `.local/learner/subjects/<subject-id>/sort-state.json` 以及本地 review-priority projection、review order 和 review queue。
- 不修改 Source、Card 内容、Question、Solution、Relation、canonical Markdown、HTML 或 learner_state。
- 不改变章节树、父子关系、canonical card order 或 card IDs。
- 每个分数都必须拆成九个可追溯维度，缺失信号不能静默当成零。
- 每张进入队列的卡都必须有理由和证据；分数不足时必须标为 `insufficient-signal`。
- 使用稳定的 card ID 作为同分时的最终排序键。
- 只使用当前 artifact version 的状态、exam report 和 check findings。
- `sort` 不修复 check finding，也不把排序结果写回 canonical learner state 或知识内容。
- 这是可重复、可覆盖的安全操作，不需要破坏性确认。

读取 [sort-contract.md](references/sort-contract.md)、[priority-model.md](references/priority-model.md)、[modes.md](references/modes.md) 和 [build-review-priority.md](playbooks/build-review-priority.md)。

## Routing

| 用户目标 | Mode 或 playbook |
| --- | --- |
| 综合判断最该先复习什么 | `default`，使用 [build-review-priority.md](playbooks/build-review-priority.md) |
| 偏向考试收益和高频内容 | `exam` |
| 偏向当前薄弱点和最近错误 | `weakness` |
| 偏向易错、易混和条件风险 | `risk` |
| 偏向前置知识和依赖覆盖 | `prerequisite` |
| 生成今晚的短队列 | `tonight`，使用 [tonight-queue.md](playbooks/tonight-queue.md) |

## State machine

~~~text
SORT_REQUEST
→ LOAD_CURRENT_ARTIFACT
→ COLLECT_VERSIONED_SIGNALS
→ SCORE_WITH_MODE
→ APPLY_STABLE_ORDER
→ WRITE_PRIORITY_PROJECTION
→ VALIDATE_RESULT
→ CLOSED
~~~

## Done gate

输出 `sort.priority.v1`，包含 artifact version、mode、权重、每张卡的九维拆解、
理由、证据、稳定 rank 和 canonical structure preservation flags。运行
`validate_priority.py`，再报告队列。不要把队列顺序描述成知识正确性或学习掌握度。
