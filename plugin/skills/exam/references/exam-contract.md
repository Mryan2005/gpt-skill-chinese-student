# Exam contract

exam measures a learner against a frozen Subject snapshot. It is not a builder, a domain model, or an audit repairer.

The original exam PDF and explanation PDF are authoritative inputs. Read them with the native PDF/page-reading capability. Read [pdf-reading.md](pdf-reading.md) before running any PDF-backed exam.

## State machine

~~~text
NEW_EXAM_REQUEST → CLEANUP_PREVIOUS_RUN → WORKSPACE_VERIFIED_CLEAN
      → LOAD_EXAM_PDF → SNAPSHOT_FROZEN → FIRST_PASS → ANSWERS_FROZEN
      → SOLUTION_RELEASED → GRADING → POSTMORTEM → CLOSED
~~~

States only move forward. A resumed task loads the existing record and continues from its state.

Read [exam-workspace.md](exam-workspace.md) before creating a new run. The previous exam workspace is disposable and must be deleted as a whole before the new PDF is loaded.

Before SNAPSHOT_FROZEN, an outdated Subject must be migrated by update. The snapshot must record migrationStatus=UP_TO_DATE. After SNAPSHOT_FROZEN, update cannot alter the snapshot or its Derived state; a later migration starts a separate exam.

## Access policy

During FIRST_PASS, allowed inputs are:

- the frozen Subject knowledge graph and its mapped evidence;
- the exam questions, figures, and instructions;
- the local answer record being written.

Forbidden inputs are Web, solution PDFs, answer keys, other notes, hidden new knowledge, and any mutation of the Subject. If the graph cannot support a question, record 图谱缺口 instead of guessing.

After ANSWERS_FROZEN, the explanation source can be released. It is comparison evidence, not retroactive learning material for the first pass.

## Ownership

exam owns the snapshot, immutable first-pass answers, grading, performance
metrics, error profile, Learning Gap Report, and Repair Requests. `review`
consumes the closed Exam Result and updates the local Learner Model. `learn` or
a domain model, such as `study-math`, executes the remediation plan. `exam`
does not write Learner Model observations or modify the tested artifact.
