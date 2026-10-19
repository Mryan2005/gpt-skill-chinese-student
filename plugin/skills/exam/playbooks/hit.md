# Exam hit: question-by-question knowledge coverage

Use `chinese-student: exam hit` to test one complete original exam against one
frozen Subject snapshot. This is a coverage audit, not a prediction of likely
exam topics and not a learner-performance review.

1. Reset only `.exam-hit/current/` with
   [reset_exam_hit_workspace.py](../scripts/reset_exam_hit_workspace.py) and
   verify that the run workspace is clean.
2. Freeze the current Subject snapshot and record its content hash before any
   question is judged. Do not add or repair knowledge during this run.
3. Read every page of the original exam PDF directly with native PDF/page
   reading. Identify every real question, including formulas, options, tables,
   figures, and subquestions. Do not sample, filter by priority, or skip
   unanswered questions.
4. For every question, record the required concepts, conditions, formulas,
   methods, algorithms, or reasoning operations. Retrieve and read the actual
   content of candidate cards, not just titles or IDs.
5. Assign exactly one `HIT`, `PARTIAL`, `MISS`, or `UNRESOLVED` status. A
   missing mapping is not a MISS when the card content independently supports
   the question. An unreadable or insufficiently evidenced question is
   `UNRESOLVED`, not `MISS`.
6. Save content excerpts, card fields, reasoning, missing knowledge, mapping
   issues, and original PDF evidence for every question. Compute full-exam
   counts only after all question records exist.
7. Verify the snapshot hash is unchanged and report the coverage matrix. Do not
   write Learner State, Exam Result, Source, or canonical knowledge.

Use [hit-contract.md](../references/hit-contract.md),
[run_hit.py](../scripts/run_hit.py), and
[validate_hit_report.py](../scripts/validate_hit_report.py). `heal exam`
consumes this report, routes real gaps to learning, and reruns `exam hit` on a
new snapshot after repairs.
