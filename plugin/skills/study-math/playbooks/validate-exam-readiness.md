# Validate exam readiness

## Use this playbook when

Use it when the user asks whether a mathematical subject graph can support an exam or wants a pre-exam audit. This playbook is read-only unless the user separately asks for repairs.

## Read

- [principles.md](../references/principles.md)
- [math-integrity.md](../references/math-integrity.md)
- [math-rendering.md](../references/math-rendering.md)
- [card-schema.md](../references/card-schema.md)
- [question-schema.md](../references/question-schema.md)

## Procedure

1. Fix the subject, record version, canonical Markdown, graph HTML, and learner-state paths.
2. Run validate_math.py and validate_math_cards.py on the actual Structured Math Records.
3. Run validate_markup.py on canonical Markdown and retained reports.
4. Check coverage, source classification, card atomicity, question primary mapping, question/solution/answer consistency, formula integrity, relation typing, and separate knowledge/question mastery.
5. Inspect the actual HTML for representative definition, theorem, method, problem-pattern, bridge, long formulas, search, relation navigation, and console errors when an HTML output exists.
6. Report metrics, failed codes, evidence paths, unresolved boundaries, and the final status.

## Gate

Report 可用于考试 only when all required gates and actual artifact checks pass. Otherwise report 学习未完成 and preserve each failure as an exam 图谱缺口. Do not repair during a read-only audit.
