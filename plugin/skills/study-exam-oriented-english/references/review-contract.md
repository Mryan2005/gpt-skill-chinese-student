# English review contract

`review` owns the PDF reading, attempt identity, evidence gate, and generic
Learner Model update. This domain model supplies language-specific diagnostics.

## Writing review

Check, in order:

1. task completion and content fidelity;
2. sentence grammar and lexical accuracy;
3. naturalness and paragraph coherence;
4. unnecessary complexity, repetition, or template dependence;
5. genre, length, and task requirements.

Report `original → issue → simple recommendation → reason`. Keep a correct
simple sentence unchanged. Do not rewrite merely to demonstrate sophistication.

## Translation review

Check missing information, wrong meaning, logic changes, key terms, literal
translation, and naturalness. A different Chinese wording is not an error by
itself. Each diagnosis points to a source fragment, learner phrase, evidence,
and preserved or lost meaning relation.

AI-generated writing or translation is material evidence only. It cannot create
or lower real-user mastery. A human submission can update Learner State only
through the existing `review user-written` gate.
