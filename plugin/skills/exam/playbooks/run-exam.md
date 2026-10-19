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
6. For each question, create separate Hit Inspector and Independent Answerer
   contexts. Read the original question, run the internal Exam Hit phase against the frozen
   snapshot, save the Hit record, then give only the original question to the
   answerer. Never pass card content, Hit status, missing knowledge, or
   research results to the answerer.
7. Save one first-pass record with `attemptStatus`, answer or explicit null,
   confidence, reasoning, phase order, and the answerer's question-only input
   policy. Hit evidence remains in the separate question `hit` record.
8. Verify every question has a completed Hit record, then verify
   `processedQuestionCount == totalQuestionCount` and
   `unprocessedQuestionCount == 0`. Freeze all first-pass records and transition
   to ANSWERS_FROZEN only when the coverage gate passes.
9. Stop. Route later explanation reading to grade-exam.

## Gate

If residualPaths is not empty, do not load the question PDF and do not enter SNAPSHOT_FROZEN or FIRST_PASS. Do not use OCR, a surrogate transcript, Web, solutions, answer keys, call learn, call study-math to add knowledge, or modify the Subject before ANSWERS_FROZEN. The prohibition applies to every delegated helper. Do not classify a question as a graph gap merely because direct mapping is missing.
