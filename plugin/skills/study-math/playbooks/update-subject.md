# Update a subject

## Use this playbook when

Use it when new material must be added to an existing mathematical subject without creating a second graph, resetting progress, or replacing earlier evidence.

## Read

- [principles.md](../references/principles.md)
- [source-schema.md](../references/source-schema.md)
- [card-schema.md](../references/card-schema.md)
- [question-schema.md](../references/question-schema.md)
- [math-integrity.md](../references/math-integrity.md)

## Procedure

1. Load the existing task state, canonical Markdown, graph HTML, learner state, design memory, and Structured Math Records.
2. Assign the new batch a source and report path. Never overwrite the original source files.
3. Run ingest-material on the new batch. Compare stable IDs and normalized fingerprints with existing records.
4. Merge only evidenced new sources, questions, cards, and relations. Keep conflicts as explicit unresolved records.
5. Preserve prior question numbers, answer provenance, learner history, and card IDs. Update progress only from new evidence.
6. Regenerate the single canonical Markdown and graph output after the records pass validation.
7. Run the full readiness and rendering checks, then append the change to task state.

## Gate

The updated subject has one canonical output, no duplicate question content, no lost formula objects, valid references, and preserved history. If the new batch creates a conflict, report the conflict instead of silently replacing the old record.
