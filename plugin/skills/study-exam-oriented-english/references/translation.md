# English-to-Chinese translation model

## Procedure

For a long or difficult sentence:

1. identify the main clause;
2. map modifiers and subordinate clauses;
3. identify logic relations and scope;
4. resolve key terms in context;
5. split the source into meaning units;
6. reorder those units into natural Chinese;
7. verify that no condition, negation, comparison, cause, uncertainty, or
   professional term was dropped or strengthened.

The final translation may differ from English word order. It must not differ in
meaning. A short, natural Chinese sentence is preferred to a literal
translation when the information and logic are preserved.

## Logic invariants

Track `negation`, `causal`, `comparison`, `condition`, `concession`, `contrast`,
`scope`, and `uncertainty` explicitly when present. The `preservedLogicRelations`
set must cover the source set. If the relation cannot be resolved from the
source, mark the translation `needs_review` rather than guessing.

## Translation feedback

Point to the source fragment and the learner's corresponding Chinese phrase.
Distinguish literal word order, missing information, wrong logic, wrong term,
and unnatural Chinese. Multiple translations may be acceptable when they
preserve the same meaning units and logic relations.
