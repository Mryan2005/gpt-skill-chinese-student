# Learn and the Local Learner Model

Before teaching a Card or Question, load the local Subject Learner Model when it
exists:

~~~text
active error patterns
effective explanation strategies
current mastery dimensions
recent observations
learning epoch
~~~

Use a Teaching Strategy Selector to choose the next teaching action. The
selector may change the order of prompts, the amount of scaffolding, the use of
visual structure, the comparison step, or the recall step. It must not change
the card's canonical meaning.

## Strategy rules

- `METHOD_SELECTION_ERROR` favors `TRIGGER_FIRST` and asks for structural
  recognition before naming a method.
- `CONDITION_CHECK` favors a precondition question before formula use.
- `SETUP` or a domain region error favors a diagram, inequalities, and model
  construction before calculation.
- `EXECUTION` favors inspection of the actual step rather than repeating the
  whole concept lesson.
- `RETRIEVAL` favors `RECALL_FIRST` and a short retrieval cue.

Domain skills define their own error codes and strategy meanings. The core does
not infer a personality, learning style, intelligence, or memory ability.

After the interaction, append one factual Observation to the local JSONL file.
Record the task stage, event, error code if observed, hints, explanation
patterns, and outcome. Do not write a stable learner claim from one event.

The Learner Model is local state. Do not copy it into Source, canonical cards,
public HTML, or Git-tracked artifacts.
