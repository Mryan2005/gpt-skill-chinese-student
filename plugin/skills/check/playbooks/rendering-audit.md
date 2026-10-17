# Rendering audit

## Use this playbook when

Markdown, formulas, search, card selection, relation navigation, HTML layout,
assets, or browser console behavior looks wrong.

## Dispatch

Run [rendering-auditor](../agents/rendering-auditor.md). Add the math auditor
for formula semantics and the retrieval auditor for real search behavior.

## Gate

Separate static syntax, rendered-page, and interaction evidence. If no actual
HTML output or browser session exists, report that scope as unverified rather
than claiming rendering success.
