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
first_pass_answer
confidence
reasoning_summary
knowledge_cards_used
retrieval_result
order
~~~

The first-pass object is immutable after ANSWERS_FROZEN. A changed answer is an appended revision with reason and timestamp. Never replace first_pass_answer with post_review_answer.

## Evidence boundary

If the learner did not find a supporting card, record retrieval failure and 图谱缺口. If the question itself is incomplete or conflicting, record QUESTION_SOURCE_ISSUE. Do not use a later official answer to rewrite the first attempt.
