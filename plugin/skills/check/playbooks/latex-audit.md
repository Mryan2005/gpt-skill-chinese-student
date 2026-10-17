# LaTeX audit

## Use this playbook when

The user asks whether formulas are syntactically valid or whether notation was
preserved from the original source.

## Dispatch

Run [latex-auditor](../agents/latex-auditor.md). Add [math-auditor](../agents/math-auditor.md)
for semantic theorem, condition, or operation checks, and add
[rendering-auditor](../agents/rendering-auditor.md) for actual page evidence.

## Gate

Keep syntax, source preservation, and visual rendering as separate findings.
Do not mark a formula correct because MathJax accepted it.
