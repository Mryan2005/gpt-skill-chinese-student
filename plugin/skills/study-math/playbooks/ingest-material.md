# Ingest material

## Use this playbook when

Use it when the user supplies new mathematical images, PDFs, textbook pages, notes, or source files and asks to add them to a math subject.

## Read

- [principles.md](../references/principles.md)
- [source-schema.md](../references/source-schema.md)
- [math-rendering.md](../references/math-rendering.md)
- [math-agents.md](../references/math-agents.md) for a multi-file batch

## Outcome

Create or extend Structured Math Records for source entities and MathObjects. Preserve source locations, page order, readable formulas, figures, question groups, and unreadable regions.

This playbook does not build final cards, choose primary cards, or solve questions. Route the result to build-cards, organize-question-set, or validate-exam-readiness as needed.

## Procedure

1. Read the target project state and inventory every supplied file in deterministic order.
2. Inspect each source in full. Record text, formulas, figures, captions, page breaks, and exact unreadable boundaries.
3. Create one Source record per source entity. Classify it before mapping it to a question.
4. Create MathObjects for formulas, matrices, roots, integrals, limits, piecewise functions, differential equations, and figures.
5. Split independent questions only when the source makes their boundaries clear. Keep an unsplit photo group as question_group until it can be split safely.
6. Preserve evidence labels and provenance. Do not fill missing content from memory or an unrelated web page.
7. Save an intake report outside canonical outputs. The main skill merges the report after the source boundary check.

## Gate

Pass only when every input has a status and source entry, every entity has an entityType, every MathObject has an ID and status, and every unresolved region is named. A source classified as unclassified remains blocked from exam readiness.
