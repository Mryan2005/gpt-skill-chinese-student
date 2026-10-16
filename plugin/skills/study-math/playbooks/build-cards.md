# Build cards

## Use this playbook when

Use it when Structured Math Records already exist and the task is to build or rebuild mathematical cards, hierarchy, or semantic relations.

## Read

- [principles.md](../references/principles.md)
- [card-schema.md](../references/card-schema.md)
- [relation-schema.md](../references/relation-schema.md)
- [question-schema.md](../references/question-schema.md)

## Procedure

1. Load modules, sources, questions, and existing cards. Keep stable IDs unless a duplicate concept must be merged with evidence.
2. Identify one independent recall task per card. Split cards that combine definitions, methods, extrema, curvature, or unrelated problem patterns.
3. Select the type that matches the task: definition, theorem, formula, method, problem-pattern, comparison, or bridge.
4. Fill the type-specific fields, recallPrompt, operationTags, sourceIds, questionIds, and atomicity metadata.
5. Enforce Card Size. Keep no more than three recommended questions; send the rest to Question Bank.
6. Build module hierarchy separately from semantic relations. Every relation has a direction, type, and mathematical why.
7. For a bridge, require real outgoing relations. A diagram without typed edges is not a bridge.
8. Run validate_math_cards.py, then validate_math.py.

## Gate

Each card answers one core recall question, points to evidence, and exposes the right type-specific fields. No card copies complete question text, and no relation depends on a vague “related” label.
