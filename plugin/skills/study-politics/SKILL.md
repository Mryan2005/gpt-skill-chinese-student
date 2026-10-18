---
name: study-politics
description: Use as the politics domain model for source-faithful political concepts, principles, canonical expressions, comparisons, confusions, timelines, policy frameworks, and exam-oriented question mappings. learn remains the workflow front door.
---

# Study politics

`study-politics` defines how political knowledge is represented and understood.
It is not a second `learn` skill and it is not a task router. `learn` selects a
playbook and loads this Derived model for a politics Subject.

## Non-negotiables

- Source and Derived content are different entities. Derived content never
  modifies, overwrites, or rewrites the original wording.
- Every Derived record traces to original material through `sourceRefs` and a
  locator.
- Textbook wording, canonical wording, AI extraction, explanations, confusions,
  and Derived question reasoning stay separate.
- Do not replace words such as "only", "fundamental", "essential", "primary",
  "core", "basis", "precondition", "determines", or "embodies" without
  evidence from the source.
- Derived cards may be deleted, rebuilt, and reorganized. Source version does
  not change as a result.
- Use politics card types. Do not force the mathematics card schema or a generic
  four-section template onto politics content.

## Card types

Politics supports at least:

~~~text
concept
principle
canonical-expression
comparison
confusion
timeline
policy-framework
problem-pattern
~~~

See [politics-cards.md](references/politics-cards.md) for fields and examples.
Read [learner-errors.md](references/learner-errors.md),
[politics-integrity.md](references/politics-integrity.md), and the platform
[Source/Derived contract](../../references/platform-contract.md) when needed.

## Learn integration

`learn` owns ingestion, topic study, question organization, Subject updates,
repair, and readiness. `study-politics` owns politics card types, wording
fidelity, relation semantics, question mapping, and politics-specific readiness
interpretation.
