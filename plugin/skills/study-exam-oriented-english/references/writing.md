# Writing model

## Objective

Help the learner express a complete exam response with language they can
understand and reproduce. The default level is `standard`: high-frequency
words, clear subject-verb-object sentences, useful coordination, and only
necessary teachable clauses.

Supported task types include:

- `application-letter`: purpose, request, suggestion, reason, and polite close;
- `graph-essay`: describe the picture or phenomenon, state the idea, explain
  causes, give a modest example, and conclude;
- `opinion-essay`: state a position, support it, handle contrast, and conclude;
- `idea-to-simple-english`: turn Chinese meaning units into independently
  usable English.

## Meaning-preserving simplification

Represent the intended message as explicit `intentUnits`. A rewrite is valid
only when every unit remains present, the stance and scope are unchanged, and
the result is grammatical and natural. Use a simpler form when it lowers the
learner's expression burden without weakening content, genre, or coherence.

Do not mechanically replace every complex sentence. Preserve a correct simple
sentence and record `unchanged: true` when revision evidence is absent.

## Expression levels

- `basic`: simple sentences and high-frequency words;
- `standard`: simple language with controlled sentence variety;
- `advanced`: additional variety only when accuracy and independent use remain
  intact.

These levels describe teaching difficulty, not exam scores or ability labels.

## Quality record

Record content completion, clarity, coherence, grammar accuracy, lexical
accuracy, genre fit, and naturalness independently. Never use advanced-word
count or sentence complexity as a proxy for quality.
