# Organize questions

## Use this playbook when

Use it when the user supplies a question set, question photos, an exam paper, solutions, or answer keys that must enter a Subject.

## Read

- [source-model.md](../references/source-model.md)
- [question-model.md](../references/question-model.md)
- [provenance.md](../references/provenance.md)

## Procedure

1. Classify question, solution, answer, figure, and unsplit group sources.
2. Split only independently identifiable questions. Preserve original number and type.
3. Store complete stems, options, figures, subparts, solutions, and answer evidence once.
4. Keep question, solution, answer, and source statuses independent.
5. Normalize identities and report duplicate or conflicting records.
6. Ask the selected domain model to choose primary concepts, card fields, or subject-specific tags.
7. Run the generic and domain validators before writing the Subject graph.

## Gate

Every question has stable identity, complete evidence or an explicit incomplete status, one domain mapping, and no duplicated full content. Metadata cannot replace a missing question.
