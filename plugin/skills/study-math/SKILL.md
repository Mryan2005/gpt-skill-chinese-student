---
name: study-math
description: Internal mathematics domain model loaded by learn for systematic topics, question records, formula-preserving cards, map repair, and readiness rules. Use learn as the user-facing cross-subject front door for ordinary math learning.
---

# Study math

`study-math` is the mathematics front door. It selects a playbook, then loads
the required mathematics contracts, agents, and executable gates. Users describe
the goal and do not need to arrange agents or validators.

## Non-negotiables

- Each card solves one mathematics problem that supports independent recall.
- Chapters, tables of contents, and overviews are module metadata. They do not
  become questions or large review cards automatically.
- Never guess, fill, or silently drop mathematics content. Preserve unreadable
  boundaries.
- Keep Source, Question, Card, and Relation as separate layers. Store complete
  question text once.
- Every question has exactly one primary card. Other knowledge points are
  secondary tags.
- Every Relation has a type, direction, and reason. Every Bridge has a real
  outgoing relation.
- Keep `sourceStatus`, `questionStatus`, `solutionStatus`, and `answerStatus`
  separate.
- Validate the real artifact, not only file existence or prompt output.

Read [principles.md](references/principles.md),
[learner-errors.md](references/learner-errors.md), and the platform
[Source/Derived contract](../../references/platform-contract.md).

## Routing

| User goal | Playbook |
| --- | --- |
| Add images, PDFs, textbooks, or notes | [ingest-material.md](playbooks/ingest-material.md) |
| Study a chapter or topic | [learn-topic.md](playbooks/learn-topic.md) |
| Organize mathematics questions | [organize-question-set.md](playbooks/organize-question-set.md) |
| Build cards and relations from records | [build-cards.md](playbooks/build-cards.md) |
| Add material to an existing Subject | [update-subject.md](playbooks/update-subject.md) |
| Repair the mathematics graph | [repair-knowledge-map.md](playbooks/repair-knowledge-map.md) |
| Check exam readiness | [validate-exam-readiness.md](playbooks/validate-exam-readiness.md) |

When a goal spans stages, choose the main playbook for the user's outcome and
let it compose the other playbooks.

## Shared contract

1. Read `AGENTS.md`, `.codex/task-state.md`, `learner_state.md`, and
   `design_memory.md` in the target project when they exist.
2. Use one Structured Math Record containing modules, cards, questions,
   relations, sources, and progress.
3. Agents write isolated reports. The main skill is the only merger for
   canonical Markdown, the knowledge graph, learner state, and task state.
4. Project mathematics records into the shared Subject artifacts. Do not create
   a second mathematics database.
5. Load only the references required by the current playbook.

## Done gate

Run the relevant `validate_math.py`, `validate_math_cards.py`, and
`validate_markup.py` checks. Verify source classification, card atomicity,
question completeness, primary mapping, formula integrity, answer evidence,
typed relations, real Markdown and HTML output, and separate knowledge and
question mastery. If a core gate fails, report `LEARNING_INCOMPLETE` and pass the
concrete graph gap to `exam`.
