# Rendering integrity

## Use this playbook when

Use it when Markdown, formulas, search, card selection, relation navigation, HTML layout, assets, or browser console behavior looks wrong.

## Procedure

1. Run the applicable Markdown/LaTeX validator on canonical Markdown and retained reports.
2. Open the actual HTML output when one exists. Inspect representative cards, long formulas, Chinese text, narrow layout, search, relation navigation, and question views.
3. Check local asset paths and browser console output.
4. Separate static validation from actual visual or interaction evidence.
5. Emit findings with the rendered location and repairOwner learn/output or the domain model.

## Gate

Do not report rendering success from source delimiters alone. If no HTML output or browser session exists, report that scope as unverified.
