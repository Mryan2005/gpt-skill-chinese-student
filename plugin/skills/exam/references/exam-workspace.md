# Exam ephemeral workspace contract

Every exam run owns one disposable workspace:

~~~text
<subject-project>/.exam/current/
├─ exam.pdf
├─ explanation.pdf
├─ snapshot.json
├─ first-pass-answers.json
├─ grading.json
├─ error-analysis.json
├─ working/
├─ pages/
└─ cache/
~~~

## Reset order

Start every new run in this order:

~~~text
NEW_EXAM_REQUEST
→ CLEANUP_PREVIOUS_RUN
→ WORKSPACE_VERIFIED_CLEAN
→ LOAD_EXAM_PDF
→ SNAPSHOT_FROZEN
→ FIRST_PASS
~~~

Delete the entire current workspace before loading the new exam PDF. Do not delete individual files by a guessed list.

The reset includes the previous exam PDF, explanation PDF, page images, OCR/transcript caches, first-pass answers, reasoning notes, snapshot, grading, error analysis, debug output, and subagent temporary files.

## Preserve boundary

The reset must not delete:

- Source Layer;
- canonical Subject Markdown or HTML;
- Derived Knowledge;
- learner_state already accepted by learn;
- question mastery or knowledge mastery already accepted by learn;
- `.local/learner/` observations, global explanation evidence, and subject
  learning epochs;
- task-state or design-memory records.

Exam history is not retained by default. A future exam-history feature must use a separate contract and directory.

## Clean verification

Before LOAD_EXAM_PDF, the record must say:

~~~text
workspace.cleanVerified = true
workspace.residualPaths = []
workspace.previousRunDeleted = true
~~~

Any residual answer, solution, snapshot, transcript, cache, or debug file blocks SNAPSHOT_FROZEN and FIRST_PASS with EXAM_WORKSPACE_NOT_CLEAN.
