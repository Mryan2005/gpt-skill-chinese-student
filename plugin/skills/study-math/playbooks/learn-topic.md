# Learn a topic

## Use this playbook when

Use it when the user wants a chapter or topic turned into an exam-ready mathematical learning path, not only transcribed.

## Read

- [principles.md](../references/principles.md)
- [card-schema.md](../references/card-schema.md)
- [question-schema.md](../references/question-schema.md)
- [relation-schema.md](../references/relation-schema.md)
- [math-integrity.md](../references/math-integrity.md)
- [math-rendering.md](../references/math-rendering.md)

## Composition

This playbook composes the narrower flows:

~~~text
ingest-material
→ organize-question-set when questions are supplied
→ build-cards
→ validate-exam-readiness
~~~

Do not ask the user to repeat these internal steps.

## Procedure

1. Establish the subject, chapter modules, source set, existing records, canonical Markdown, graph HTML, and learner state.
2. Complete source intake before writing card highlights. Keep course navigation in modules and card hierarchy.
3. Derive independent recall tasks from the material and questions. Choose the smallest suitable Card Type.
4. Build both navigation hierarchy and typed semantic relations. Do not replace the formal course skeleton with only a method graph.
5. Map representative questions by real solving action. Keep the full question in Question Bank and show only selected question IDs on a card.
6. Project the validated records into the one canonical subject output.
7. Run the exam-readiness gate. Record concrete gaps instead of claiming completion from page existence.

## Gate

The topic is ready only when coverage, concepts, conditions, boundaries, question mappings, relations, provenance, formulas, rendering, and active gaps all pass. Otherwise report 学习未完成.
