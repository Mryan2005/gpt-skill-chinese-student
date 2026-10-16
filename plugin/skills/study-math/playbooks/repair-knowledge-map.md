# Repair a knowledge map

## Use this playbook when

Use it when an existing mathematical graph has giant cards, metadata questions, duplicate questions, missing formulas, wrong mappings, vague relations, or inconsistent solutions.

## Read

- [principles.md](../references/principles.md)
- [card-schema.md](../references/card-schema.md)
- [question-schema.md](../references/question-schema.md)
- [relation-schema.md](../references/relation-schema.md)
- [math-integrity.md](../references/math-integrity.md)
- [math-rendering.md](../references/math-rendering.md)

## Procedure

1. Snapshot the current records, canonical output, and readiness state. Do not repair while measuring the baseline.
2. Run validate_math.py and validate_math_cards.py. Group failures by their first wrong boundary.
3. Repair in source-to-output order: source classification, question identity, MathObjects, question mapping, cards, relations, canonical output.
4. Split broad cards by independent recall task. Keep stable IDs for retained concepts and record merges explicitly.
5. Replace metadata questions with their source records. Keep real incomplete questions and mark their status.
6. Rebuild primary mappings from solving actions. Recompute duplicate fingerprints and relation reasons.
7. Regenerate the unified output and rerun every affected gate.
8. Report baseline failures, repairs, remaining gaps, and actual rendered checks separately.

## Gate

The repaired graph must pass the requested structural gates and preserve unresolved evidence. Do not call a repair complete because the page opens or the question count looks unchanged.
