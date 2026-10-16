# Retrieval integrity

## Use this playbook when

Use it when the user cannot find a concept, a question, a chapter, or a relation through the Subject search and navigation.

## Procedure

1. Build a read-only retrieval matrix from stable IDs, titles, confirmed aliases, source terms, question terms, and relation targets.
2. Run exact-title, confirmed-alias, chapter-term, question-term, and relation-target probes.
3. Record query, expected ID, hit IDs, search actions, card selections, and visible target sections.
4. Classify zero hits, ambiguous hits, wrong mappings, missing index entries, and unmeasured interaction counts.
5. Emit findings with repairOwner learn/retrieval or the domain model.

## Gate

A static matrix cannot claim that a real interaction was measured. Report unmeasured searches separately from observed failures.
