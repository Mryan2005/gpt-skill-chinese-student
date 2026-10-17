---
name: relearn
description: Use for an explicitly confirmed destructive rebuild of a Subject's Derived learning state from preserved Source records. Do not use for ordinary learning, Subject updates, schema migration, or deleting a Subject.
---

# 中式学生：重学入口

relearn 丢弃当前 Subject 的 Derived 学习结果，再基于保留下来的 Source 调用 learn 和领域模型重新构建。它不是继续学习，也不是 update。

## Non-negotiables

- 先识别 Subject 并生成影响范围，不能直接删除。
- 必须向用户展示 delete/preserve 清单，并等待明确确认。
- 只能删除 Derived、artifact、progress、index 和旧渲染产物。
- Source、Source Records、原始题目、官方答案、原始解析和 provenance 永远保留。
- 删除前生成一次性 reset manifest。实际删除必须显式使用 --apply。
- 删除后验证 Derived 区域为空，再调用 learn 和领域模型。
- 重建完成后必须调用 check。任何 blocker/error 都不能报告完成。
- relearn 不等于 reset-subject；本 skill 永远不删除 Source。

## State machine

~~~text
RELEARN_REQUESTED
→ IMPACT_ANALYZED
→ WAITING_FOR_USER_CONFIRMATION
→ CONFIRMED
→ DELETE_DERIVED_STATE
→ VERIFY_CLEAN
→ CALL_LEARN
→ LOAD_DOMAIN_MODEL
→ REBUILD
→ CHECK_FULL_AUDIT
→ RELEARN_COMPLETE
~~~

没有明确确认时停在 WAITING_FOR_USER_CONFIRMATION。

## Routing

- 影响分析：[impact-analysis.md](playbooks/impact-analysis.md)
- 确认和重置：[confirm-and-reset.md](playbooks/confirm-and-reset.md)
- 重建：[rebuild.md](playbooks/rebuild.md)
- 完成验证：[validate.md](playbooks/validate.md)

## Done gate

reset manifest 已确认、Source 未变、Derived 已清空并重建、当前领域模型已加载、
`check full-audit` 返回 `PASS` 或 `PASS_WITH_WARNINGS`，且 learner_state 由 learn
重新生成后，才能报告 RELEARN_COMPLETE。任何 blocker、error 或 BLOCKED 都必须报告
RELEARN_WITH_ERRORS。
