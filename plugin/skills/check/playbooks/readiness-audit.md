# Readiness audit

## Use this playbook when

The user asks whether a Subject can be used for review or an exam.

## Procedure

1. Read the Subject and domain readiness contract.
2. Select every auditor required by that contract, including source,
   structure, coverage, question, solution, relation, provenance, rendering,
   and retrieval checks as applicable.
3. Run the Finding Merger and record skipped or unmeasured checks explicitly.
4. Read `learner_state` and task-state for active gaps. Do not infer mastery
   from page existence, question count, or a clean render.
5. Mark the Subject not ready when a blocker exists or a required audit was not
   executed.

## Gate

Readiness is a conclusion about one inspected artifact version. It is not a
repair command and it is not a promise that future source changes remain valid.
