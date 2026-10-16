# Readiness

## Use this playbook when

Use it when the user asks whether a Subject can be used for review or an exam.

## Procedure

1. Run source, knowledge, question, relation, retrieval, and rendering checks required by the Subject and domain contract.
2. Read learner_state and task-state for active gaps. Do not infer mastery from page existence or question count.
3. Check coverage, clarity, conditions, boundaries, question evidence, provenance, formula rendering, relations, and separate knowledge/question mastery.
4. Aggregate findings by severity. Any blocker or required unexecuted check prevents 可用于考试.
5. Emit a read-only report with root causes and repair owners.

## Gate

Readiness is a conclusion about the inspected artifact version. It is not a repair command and not a promise that future source changes remain valid.
