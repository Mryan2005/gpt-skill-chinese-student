# Priority model

The model uses nine signals. Each signal is a number from 0 through 100 or
`null` when the current evidence does not support a value.

| Dimension | Meaning | Typical evidence |
| --- | --- | --- |
| `exam_importance` | Core or high-yield value for the target exam | domain contract, exam blueprint |
| `error_risk` | Risk that the learner will make a correctness or condition error | check findings, error taxonomy, domain risk fields |
| `dependency_weight` | Importance as a prerequisite for later cards | typed prerequisite relations, downstream count |
| `user_weakness` | Current learner weakness | learner state, knowledge mastery |
| `recent_exam_errors` | Recent errors that involve this card | current exam result, or an exam-gap record accepted into learner state |
| `coverage_gap` | Missing or partial source-to-card coverage | check coverage findings, source map |
| `confusion_density` | Number and strength of common confusions | typed often-confused relations, question mappings |
| `recall_difficulty` | Difficulty of active recall for this card | learner state, recall outcomes |
| `question_frequency` | Frequency and spread in the question set | question records, domain frequency data |

The domain model supplies domain meaning. `sort` supplies the common scoring
shape and evidence requirements. It must not treat a high score as proof that a
card is correct or mastered.

## Reason codes

Use these codes when the matching signal supports them:

~~~text
high_exam_importance
high_error_risk
high_dependency
user_weakness
recent_exam_error
coverage_gap
often_confused
hard_to_recall
high_question_frequency
insufficient_signal
~~~

Every reason has a human-readable label and at least one evidence location.
