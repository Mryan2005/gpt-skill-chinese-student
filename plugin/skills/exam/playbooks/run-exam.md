# Run an exam

## Use this playbook when

Use it when the user wants to begin or complete a closed-book exam against the current Subject.

## Read

- [exam-contract.md](../references/exam-contract.md)
- [exam-workspace.md](../references/exam-workspace.md)
- [pdf-reading.md](../references/pdf-reading.md)
- [answer-record.md](../references/answer-record.md)
- [error-taxonomy.md](../references/error-taxonomy.md)

## Procedure

1. Enter CLEANUP_PREVIOUS_RUN. Reset the exact .exam/current workspace with reset_exam_workspace.py --apply.
2. Verify that the workspace is empty and record previousRunDeleted=true, cleanVerified=true, and residualPaths=[].
3. Load the exact Subject artifact and readiness state.
4. Load the original question PDF directly and only then transition to LOAD_EXAM_PDF.
5. Create and freeze an Exam Snapshot before answering.
6. Enter FIRST_PASS. Use only the snapshot and questions.
7. Save one first-pass record per question with answer, confidence, card IDs, retrieval result, original PDF page, and evidence boundary.
8. Freeze all first-pass answers and transition to ANSWERS_FROZEN.
9. Stop. Route later explanation reading to grade-exam.

## Gate

If residualPaths is not empty, do not load the question PDF and do not enter SNAPSHOT_FROZEN or FIRST_PASS. Do not use OCR, a surrogate transcript, Web, solutions, answer keys, call learn, call study-math to add knowledge, or modify the Subject before ANSWERS_FROZEN. The prohibition applies to every delegated helper.
