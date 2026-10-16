# Update an existing Subject

## Use this playbook when

Use it when new material must be added to an existing Subject without creating a second canonical graph or resetting learner history.

## Read

- [knowledge-model.md](../references/knowledge-model.md)
- [source-model.md](../references/source-model.md)
- [question-model.md](../references/question-model.md)
- [provenance.md](../references/provenance.md)

## Procedure

1. Load task state, canonical Markdown, graph HTML, learner state, design memory, and existing Subject records.
2. Run ingest-material on the new batch and preserve original files.
3. Compare stable IDs and normalized fingerprints with existing records.
4. Merge only evidenced sources, questions, nodes, relations, and progress changes.
5. Preserve old question numbers, answer provenance, learner history, and domain-specific IDs.
6. Regenerate the single Subject output and run validate-readiness.
7. Record the update in task-state.

## Gate

The Subject still has one canonical output, preserved history, valid references, no duplicate question content, and no silently replaced evidence.
