# Answer record

## Snapshot

Every exam record stores:

- exam ID and Subject ID;
- frozen snapshot ID, artifact version, graph path, and freeze time;
- source question path/version;
- state and access policy.

The snapshot is immutable for the run. A later Subject update starts a new exam.

## First-pass answer

Each question stores:

~~~text
question_id
original_number
type
attempt_status
first_pass_answer
confidence
reasoning_summary
knowledge_cards_used
retrieval_result
order
~~~

`attempt_status` distinguishes `ANSWERED`, `UNANSWERED_BY_LEARNER`,
`BLOCKED_BY_UNREADABLE_QUESTION`, `BLOCKED_BY_SOURCE`,
`BLOCKED_BY_GRAPH_KNOWLEDGE_GAP`, `BLOCKED_BY_EXAM_SYSTEM`, and
`PARTIAL_ANSWER`. A missing direct mapping is not an attempt status.

For every readable question, record a retrieval object with
`directMappingAvailable`, `attempted`, queries, candidate cards, selected cards,
result, and evidence. `FOUND`, `PARTIAL_FOUND`, `NOT_FOUND`, and
`NOT_ATTEMPTED` are distinct retrieval results. Normal FIRST_PASS processing
must not leave readable questions at `NOT_ATTEMPTED`.

The first-pass object is immutable after ANSWERS_FROZEN. A changed answer is an appended revision with reason and timestamp. Never replace first_pass_answer with post_review_answer.

## Evidence boundary

If broad retrieval over the frozen Subject finds no usable knowledge, record a
graph knowledge gap with retrieval evidence. Do not treat missing direct mapping
as retrieval failure. If the question itself is incomplete or conflicting,
record a source blocker. Do not use a later official answer to rewrite the
first attempt.
