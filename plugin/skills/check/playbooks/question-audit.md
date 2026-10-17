# Question audit

## Use this playbook when

Questions are missing, duplicated, incomplete, grouped incorrectly, mapped to
the wrong card, or inconsistent with their recorded answer state.

## Dispatch

Run [question-auditor](../agents/question-auditor.md),
[solution-auditor](../agents/solution-auditor.md), and the applicable
[math-auditor](../agents/math-auditor.md) or subject-domain contract. Merge
their findings without remapping the questions.

## Gate

Preserve every real incomplete question and identify the earliest wrong
boundary. Do not solve, rewrite, or silently choose between conflicting answers
during a question audit.
