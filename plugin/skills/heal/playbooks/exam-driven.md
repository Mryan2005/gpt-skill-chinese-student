# Exam-driven iteration

Use `chinese-student: heal exam-driven` when a user supplies a real exam,
practice paper, or chapter test and wants the learning artifact pressure-tested.

1. Reset only `.heal/current/exam-driven/`. Preserve the original PDF and any
   historical heal runs.
2. Read the original PDF pages directly with native PDF/page capability. Do not
   use OCR, OCR transcripts, web answers, or delegated OCR. Mark unreadable
   pages/questions instead of guessing.
3. Identify only real questions with a clear prompt and preserve page/source
   provenance. Do not ingest headings, outlines, or incomplete fragments.
   For failed identification, create one recovery task per question and
   distinguish boundary, incomplete-text, source, unreadable, mapping, card,
   knowledge, solution-evidence, and answer-provenance failures.
4. Reuse the Exam-internal Hit phase against the same frozen graph snapshot for
   every question. Build the baseline from its complete HIT/PARTIAL/MISS/
   UNRESOLVED report, plus solution coverage, formula integrity, answer
   provenance, retrieval results, and existing check status. Do not use a
   preselected focus list.
5. Split reliable questions into an iteration set and an independent holdout
   set after the full Hit report exists. If the sample is too small, report
   insufficient generalization evidence.
6. Run a non-consuming read-only `check` before the repair round. Evaluate the
   current artifact, diagnose root causes, and route repairs to existing
   `check`, `fix`, `learn`, or `amend` contracts. `heal` coordinates; it does
   not implement their repair logic.
7. Call the existing `$chinese-student:optimize` Skill exactly once for the round, even when it
   produces a no-op. Apply only safe authorized migrations; record high-risk
   merge/split recommendations without silently applying them.
8. Re-run the Exam-internal Hit phase on the new frozen snapshot, then re-evaluate the iteration
   set and holdout set, run the non-consuming
   read-only `check` after the round, validate schemas/formulas/relations/
   rendering, and record coverage/quality deltas, regressions, and stability.
9. Keep `hitBefore` and `hitAfter` separate; source recovery and enrichment are
   not evidence that the original frozen graph already contained the support.
10. Stop at convergence, two rounds without meaningful progress, regression,
   optimization oscillation, evidence/permission blockage, or at most five
   repair rounds. Five rounds is not success.

The report must preserve the uploaded PDF as immutable Source, never modify a
frozen Exam Result, never update Learner State, and distinguish a system
knowledge improvement from memorizing a tested answer.
