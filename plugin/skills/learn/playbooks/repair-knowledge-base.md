# Repair a knowledge base

## Use this playbook when

Use it when a Subject graph has giant cards, metadata questions, duplicate content, wrong mappings, broken relations, missing source evidence, or unreadable output.

## Read

- [knowledge-model.md](../references/knowledge-model.md)
- [question-model.md](../references/question-model.md)
- [provenance.md](../references/provenance.md)

Also read the selected domain model and its repair playbook. For mathematics, use study-math/playbooks/repair-knowledge-map.md.

## Procedure

1. Snapshot the current records, graph, canonical Markdown, and readiness state.
2. Run generic and domain validators before changing records.
3. Group failures by the first wrong boundary: source, question identity, domain mapping, relation, output, or rendering.
4. Repair in source-to-output order. Do not add a render-layer filter for a source classification error.
5. Preserve stable IDs, unresolved questions, source conflicts, and learner history.
6. Regenerate the unified output and rerun every affected Gate.
7. Report baseline failures, repairs, remaining gaps, and actual artifact checks separately.

## Gate

Repair is complete only when the requested structural and output checks pass without deleting real incomplete material or creating a second Subject.
