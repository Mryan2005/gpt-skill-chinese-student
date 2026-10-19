# Learn a topic

## Use this playbook when

Use it when the user wants a chapter or topic turned into an exam-ready Subject graph.

## Read

- [knowledge-model.md](../references/knowledge-model.md)
- [question-model.md](../references/question-model.md)
- [provenance.md](../references/provenance.md)

## Composition

~~~text
ingest-material
→ selected domain model
→ question mapping when questions exist
→ validate-readiness
~~~

For mathematics, load study-math and choose the matching math playbook. For
exam-oriented English writing or English-to-Chinese translation, load
study-exam-oriented-english and choose its writing or translation contract.
Do not add domain card or language rules to this playbook.

## Procedure

1. Establish Subject, modules, sources, current graph, canonical Markdown, and learner state.
2. Complete source intake before deriving summaries, highlights, or domain cards.
3. Preserve formal chapter navigation and stable IDs. Let the domain model define the internal card shape.
4. Map available questions by real tested knowledge and preserve full question evidence.
5. Generate the one Subject output and update persistent learning state.
6. Run validate-readiness and report concrete gaps.

## Gate

Coverage, concept clarity, question readiness, relation integrity, provenance, notation, rendering, and active gaps all pass. Otherwise report 学习未完成.
