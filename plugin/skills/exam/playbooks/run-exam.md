# Run an exam

## Use this playbook when

Use it when the user wants to begin or complete a closed-book exam against the current Subject.

## Read

- [exam-contract.md](../references/exam-contract.md)
- [answer-record.md](../references/answer-record.md)
- [error-taxonomy.md](../references/error-taxonomy.md)

## Procedure

1. Load the exact Subject artifact and readiness state.
2. Create and freeze an Exam Snapshot before answering.
3. Read the question source. Enumerate every question, figure, option, formula, and page boundary.
4. Enter FIRST_PASS. Use only the snapshot and questions.
5. Save one first-pass record per question with answer, confidence, reasoning, card IDs, retrieval result, and evidence boundary.
6. Freeze all first-pass answers and transition to ANSWERS_FROZEN.
7. Stop. Route later explanation reading to grade-exam.

## Gate

Do not release solutions, use Web, call learn, call study-math to add knowledge, or modify the Subject before ANSWERS_FROZEN.
