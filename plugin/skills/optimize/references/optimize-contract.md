# Optimize contract

`optimize` operates on a Derived graph and produces a plan before any write.
The plan is reproducible from the current artifact fingerprint and is safe to
discard. Applying a plan requires the same fingerprint and an explicit
authorization.

## Operation classes

| Operation | Meaning | Default risk | Default action |
| --- | --- | --- | --- |
| `exact_duplicate` | Same normalized card content and identity evidence | low | recommend a stable alias migration |
| `fragmented_merge` | Fragments are explicitly grouped as one concept | high | require semantic review and confirmation |
| `semantic_merge` | Two cards appear semantically equivalent | high | recommend only; never infer from titles alone |
| `oversized_split` | One card contains multiple independently recallable cores | high | require a domain-aware split plan |
| `related_but_distinct` | Cards are related but must remain separate | low | no-op with an explanatory relation |
| `uncertain` | Evidence is insufficient or conflicting | high | block and preserve the current graph |

## Migration safety

An applied migration must record old and new IDs, question-mapping remaps,
relation endpoint remaps, aliases, and any Learner State references affected.
Learner evidence is not recomputed or deleted. A referential alias is the
preferred way to keep historical evidence resolvable without rewriting it.

The following are immutable:

- original files and Source Records;
- official answers and explanations;
- frozen Exam Results and attempt history;
- Learner State observations, mastery evidence, and self-reports.

If a semantic merge or split cannot provide a complete migration and validation
record, leave it as `RECOMMEND` or `BLOCKED`. Passing a schema validator is not
evidence that the proposed knowledge change is correct.

## Stability gate

Compare target IDs and operation class across rounds. A merge followed by a
split (or the reverse) for the same targets without new evidence is
`OPTIMIZATION_OSCILLATION` and must stop the Heal loop. Repeated identical
recommendations without new evidence are stalled, not progress.
