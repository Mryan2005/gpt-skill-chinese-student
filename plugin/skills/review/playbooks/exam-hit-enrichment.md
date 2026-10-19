# Review Exam Hit enrichment

This playbook is shared by `exam-result` and `user-written`. It consumes a
validated `exam.hit.report.v1` created from the complete original PDF and a
frozen graph snapshot.

1. Keep the before snapshot and its question-level `HIT/PARTIAL/MISS/
   UNRESOLVED` records immutable.
2. Group actual card-content anchors into one Annotation Overlay. A highlight
   must identify the card field, excerpt, content hash, question IDs, hit
   status, snapshot ID, and evidence references.
3. Classify gaps as mapping, incomplete content, missing knowledge, missing
   relation, insufficient source, answer conflict, or unreadable question.
4. Build evidence-backed research queries from the gap, not from a guessed
   answer. When network search is available, search authoritative sources and
   record the returned pages as provenance-complete External Supplements.
5. Produce `learn` handoffs for reliable supplements. `review` does not write
   canonical cards or create a parallel graph.
6. After a validated learn update, run `exam hit` on a new snapshot and record
   before/after coverage. Mark new support `enriched_exam_coverage`; never
   relabel it as an original exam hit.

If research is unavailable or evidence is insufficient, keep the gap open and
report it. Do not fabricate a source, answer, card, or complete Hit.
