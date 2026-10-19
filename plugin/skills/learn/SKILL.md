---
name: learn
description: Use as the cross-subject learning front door for new material, topic study, question-set organization, subject updates, knowledge-base repair, and exam-readiness checks. It routes domain-specific work to the appropriate subject model.
---

# Learn

`learn` is the front door for learning work. It understands the user's goal,
chooses a playbook, and loads a domain model when needed. Users describe the
goal. They do not need to name agents, schemas, or validators.

## Non-negotiables

- Each Subject has one canonical Markdown file, one knowledge graph, and one
  persistent learner state.
- Keep Source, Knowledge Node, Question, Relation, and Progress as separate
  layers.
- Classify sources before placing them in a question bank or knowledge graph.
  Preserve unreadable and unclassified boundaries.
- Never merge original material, supplements, Derived answers, readable official
  explanations, and unresolved content silently.
- Domain models own card structure. `learn` does not force every subject into
  one card schema.
- Agents write isolated reports. The main `learn` skill is the only merger.
- Validate structure, sources, Markdown, LaTeX, rendered output, and exam
  readiness before reporting completion.
- Keep the Local Learner Model private and evidence-based. Do not infer
  personality or psychological traits.

Read [common.md](references/common.md), [knowledge-model.md](references/knowledge-model.md),
[question-model.md](references/question-model.md), [provenance.md](references/provenance.md),
[learner-model.md](references/learner-model.md),
[learner-model-contract.md](../../references/learner-model-contract.md), and
[platform-contract.md](../../references/platform-contract.md) as needed. Keep
subject-specific rules out of this front door.

## Routing

| User goal | Playbook |
| --- | --- |
| Add images, PDFs, textbooks, or notes | [ingest-material.md](playbooks/ingest-material.md) |
| Study a chapter or topic | [learn-topic.md](playbooks/learn-topic.md) |
| Organize a question set or question photos | [organize-questions.md](playbooks/organize-questions.md) |
| Add material to an existing Subject | [update-existing-subject.md](playbooks/update-existing-subject.md) |
| Repair a confused, duplicated, or unreachable knowledge base | [repair-knowledge-base.md](playbooks/repair-knowledge-base.md) |
| Check exam readiness | [validate-readiness.md](playbooks/validate-readiness.md) |
| Build a review queue | Use the separate [sort](../sort/SKILL.md) skill. Do not reorder canonical cards in `learn`. |

Choose a playbook from the user's goal, then choose a domain model from the
Subject. Mathematics work reads `study-math`; politics work reads
`study-politics`; postgraduate English writing and English-to-Chinese
translation read `study-exam-oriented-english`. Future subjects can add their
own domain models.

## Shared contract

1. Read `AGENTS.md`, `.codex/task-state.md`, `learner_state.md`, and
   `design_memory.md` in the target project when they exist.
2. Keep one Subject record and one unified output. A domain intermediate record
   is not a second source of truth.
3. For complex batches, read [agent-contract.md](references/agent-contract.md)
   and save each agent report in an isolated directory.
4. Load only the references required by the current playbook.
5. Write learning state to persistent files. Do not depend on conversation
   memory for sources, exclusions, mappings, or completion state.
6. Write post-teaching observations only to `.local/learner/`.

## Done gate

Run the validators required by the current playbook and domain model. Check
source coverage, entity classification, stable IDs, question mappings,
relations, provenance, Markdown, LaTeX, and real output. If a core gate fails,
report `LEARNING_INCOMPLETE` with the concrete gap and pass it to `exam`.
Report exam readiness only after the real artifact and every required gate pass.
