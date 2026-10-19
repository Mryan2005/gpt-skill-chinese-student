# Grading and metrics

## Release order

Read official answers and solutions only after every first-pass answer is saved and frozen. Keep these fields separate:

~~~text
first_pass_answer
official_answer
post_review_answer
~~~

Official solution text may be incomplete or conflicting. Preserve the readable boundary and provenance.

## Performance

Report at least:

~~~text
correct / total
percentage
answered
wrong
unansweredByLearner
blockedUnreadable
blockedSource
blockedGraphKnowledgeGap
blockedSystem
partial
~~~

## Knowledge coverage

Measure the knowledge used by the exam:

~~~text
cards_in_exam
correctly_used_cards
incorrectly_used_cards
unretrieved_cards
~~~

## Graph effectiveness

Separate graph availability from learner use:

~~~text
questions_needing_knowledge
knowledge_found
knowledge_correctly_applied
retrieval_success_rate
application_success_rate
direct_mapping_available
retrieval_without_direct_mapping_succeeded
retrieval_failure
graph_knowledge_gap
~~~

Do not infer knowledge mastery from one correct question. Do not infer graph quality from the learner score alone.

`exam hit` is separate from these learner-performance metrics. It tests whether
the frozen graph content can support each complete question, including a new
derivation or calculation. It does not require a learner answer and does not
turn an unanswered question into a learner error.
