# Organize a question set

## Use this playbook when

Use it when the user supplies many mathematical questions, a question photo batch, a test paper, or an answer/solution set that must enter an existing or new subject graph.

## Read

- [principles.md](../references/principles.md)
- [source-schema.md](../references/source-schema.md)
- [question-schema.md](../references/question-schema.md)
- [math-integrity.md](../references/math-integrity.md)

## Procedure

1. Classify the input as independent questions, solutions, answer keys, figures, or an unsplit question group.
2. Preserve the original number and type. Assign one stable Question ID to each independent question.
3. Store the complete stem, options, figures, subparts, MathObjects, solution fragments, and answer evidence once.
4. Mark question, solution, and answer status independently. Keep incomplete questions instead of deleting them.
5. Compare the question, solution, and answer semantically. Flag mismatches and missing evidence.
6. Read the actual solving action before selecting one primaryCardId. Add secondaryCardIds only for real supporting operations.
7. Normalize the question fingerprint and report duplicates. Do not copy the full question into cards.
8. Run validate_math.py and repair the record at the earliest failed boundary.

## Gate

Every stored question has one primary card, valid secondary tags, stable provenance, explicit completeness status, and no duplicated full content. A chapter overview, question group, or answer-only source cannot enter the Question Bank as a question.
