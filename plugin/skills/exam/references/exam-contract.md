# Exam contract

exam measures a learner against a frozen Subject snapshot. It is not a builder, a domain model, or an audit repairer.

## State machine

~~~text
READY → SNAPSHOT_FROZEN → FIRST_PASS → ANSWERS_FROZEN
      → SOLUTION_RELEASED → GRADING → POSTMORTEM → CLOSED
~~~

States only move forward. A resumed task loads the existing record and continues from its state.

## Access policy

During FIRST_PASS, allowed inputs are:

- the frozen Subject knowledge graph and its mapped evidence;
- the exam questions, figures, and instructions;
- the local answer record being written.

Forbidden inputs are Web, solution PDFs, answer keys, other notes, hidden new knowledge, and any mutation of the Subject. If the graph cannot support a question, record 图谱缺口 instead of guessing.

After ANSWERS_FROZEN, the explanation source can be released. It is comparison evidence, not retroactive learning material for the first pass.

## Ownership

exam owns the snapshot, immutable first-pass answers, grading, performance metrics, error profile, Learning Gap Report, and Repair Requests. learn consumes Repair Requests. A domain model, such as study-math, decides the domain-specific repair.
