# Error taxonomy

Use one or more evidence-backed error types per graded question:

~~~text
KNOWLEDGE_MISSING
RETRIEVAL_FAILURE
CONCEPT_CONFUSION
CONDITION_MISSED
METHOD_SELECTION_ERROR
EXECUTION_ERROR
READING_ERROR
MEMORY_FAILURE
CARELESS_ERROR
TIME_FAILURE
QUESTION_SOURCE_ISSUE
~~~

The generic taxonomy describes the learner or source outcome. A domain model may add subtypes. For mathematics, study-math may add formula usage error, theorem condition omission, transformation error, integral-boundary error, probability translation error, proof-chain break, or method-selection detail.

## Repair routing

- KNOWLEDGE_MISSING → learn plus the domain model;
- RETRIEVAL_FAILURE → learn retrieval/index repair;
- METHOD_SELECTION_ERROR → domain problem-pattern or bridge repair;
- CONDITION_MISSED → domain theorem/method condition repair;
- EXECUTION_ERROR or CARELESS_ERROR → learner_state and targeted practice;
- QUESTION_SOURCE_ISSUE → learn source/question intake;
- MEMORY_FAILURE → learner_state and recall scheduling.

exam emits the route as a Repair Request. It does not apply it.
