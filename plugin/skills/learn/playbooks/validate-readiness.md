# Validate readiness

## Use this playbook when

Use it when the user asks whether a Subject can support an exam or wants a read-only pre-exam audit.

## Read

- [knowledge-model.md](../references/knowledge-model.md)
- [question-model.md](../references/question-model.md)
- [provenance.md](../references/provenance.md)
- [common.md](../references/common.md)

Also read the selected domain model's readiness contract and validators.

## Procedure

1. Fix the Subject, record version, canonical Markdown, graph HTML, and learner-state paths.
2. Run generic validators and the domain validator on the actual records.
3. Run Markdown/LaTeX checks on canonical Markdown and retained reports.
4. Check source coverage, entity classification, stable IDs, question mapping, relations, provenance, progress, and active gaps.
5. Inspect the actual HTML for search, selection, relation navigation, formulas, narrow layout, and console errors when an HTML output exists.
6. Report metrics, failure codes, evidence paths, unresolved boundaries, and final status.

## Gate

This playbook is read-only by default. Report 可用于考试 only when all required generic and domain gates pass. Otherwise report 学习未完成 and preserve each failure as exam 图谱缺口.
