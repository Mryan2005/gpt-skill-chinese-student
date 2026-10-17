# Relearn contract

## Delete

Default delete set:

~~~text
Derived cards
relations
question mappings
derived solutions
canonical Markdown
knowledge-network HTML
learner_state and mastery
old indexes
old render outputs
~~~

## Preserve

Always preserve:

~~~text
Source Layer
original PDFs and images
original textbook text
original questions
official answers and explanations
Source Records
provenance

The Learner Layer is separate from Derived. Preserve
`.local/learner/global/observations.jsonl` and global explanation evidence.
Keep subject observations with a new `learningEpoch`; rebuild subject Error
Model, Mastery, Explanation Strategy state, and `sort-state.json` from the
preserved local evidence. Do not delete the Learner Layer during Derived reset.
~~~

## Confirmation

The impact report must name the Subject, delete paths, preserve paths, estimated counts, and the loss of current Derived state. The user must explicitly confirm after seeing that report. A vague earlier request does not count as confirmation.

## Ownership

relearn owns reset orchestration. learn consumes the preserved Source and rebuilds the common Subject. study-math or study-politics owns domain Derived construction. check audits the new result. exam records only the rebuilt state after readiness. Old subject sort state is invalidated before the new epoch is built.
