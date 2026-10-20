---
name: study-exam-oriented-english
description: Internal exam-oriented English domain model loaded by learn for simple accurate writing and natural Chinese translation. Use learn as the user-facing workflow front door.
---

# Study exam-oriented English

`study-exam-oriented-english` defines the cognition and record structure for
postgraduate English writing and English-to-Chinese translation. `learn` owns
ingestion, routing, persistence, and the shared Subject; this Skill owns the
language-domain meaning, expression functions, revision evidence, and
translation invariants.

## Core principle

**Simple Language, Clear Meaning, Accurate Expression.** Prefer language the
learner can understand and use independently. Simplicity never permits lost
meaning, changed logic, false certainty, grammatical error, or failure to meet
the exam task.

Do not optimize for advanced-word count, sentence complexity, ornate style, or
万能模板. A complex form is acceptable when it is more accurate, natural, or
useful for the learner and remains teachable.

## Routing

| Goal | Domain playbook |
| --- | --- |
| Turn a Chinese idea into usable English | [writing.md](references/writing.md) |
| Practice an application or graph essay | [writing.md](references/writing.md) |
| Parse and translate a long sentence | [translation.md](references/translation.md) |
| Diagnose a writing or translation attempt | [review-contract.md](references/review-contract.md) |
| Generate a practice PDF | [integrations.md](references/integrations.md) |
| Pressure-test missing language knowledge | [integrations.md](references/integrations.md) |

## Non-negotiables

- Keep Source, Derived cards, questions, answers, and learner observations
  separate. Never rewrite the original English source.
- Preserve content requirements, logic relations, negation, causality,
  comparison, conditions, uncertainty, scope, and key terminology.
- Keep a correct, natural simple sentence when there is no evidence that it
  needs revision. Every change needs a sentence-level reason.
- Distinguish official scoring evidence, model teaching feedback, and
  expression-difficulty guidance. A model estimate is not an official score.
- Keep writing quality dimensions separate: content completion, clarity,
  coherence, grammar, lexical accuracy, genre fit, and naturalness.
- Keep translation quality dimensions separate: semantic accuracy, information
  completeness, logic, Chinese fluency, and word choice.
- A user-written attempt may update the Learner Model only through `review`'s
  human-evidence gate. AI answers and model-generated examples never do so.

Read [english-cards.md](references/english-cards.md),
[integrity.md](references/integrity.md), and the shared
[Source/Derived contract](../../references/platform-contract.md). Validate
records with [validate_english.py](scripts/validate_english.py).

## Done gate

The shared Subject contains traceable language cards and examples, preserved
meaning units, explicit logic relations, sentence-level review evidence, and
practice/review handoff fields. If a simplification or translation cannot be
shown to preserve meaning, keep it unresolved instead of claiming success.
