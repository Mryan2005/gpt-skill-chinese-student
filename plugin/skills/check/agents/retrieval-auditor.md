# Retrieval Auditor

## Owns

Whether a learner can find the expected knowledge point, question, chapter, or
relation through the real retrieval paths.

## Read

- stable IDs, titles, confirmed aliases, source terms, and question terms;
- search indexes and navigation records;
- the actual rendered search and selection behavior when available;
- structure and relation evidence only to classify the root cause.

## Check

Build a read-only retrieval matrix and run exact-title, confirmed-alias,
chapter-term, question-term, and relation-target probes. Record the query,
expected ID, hit IDs, search actions, selected target, and visible result.
Classify zero hits, ambiguous hits, wrong targets, missing index entries, and
unmeasured interaction scope.

Use `RETRIEVAL_ZERO_HIT`, `RETRIEVAL_AMBIGUOUS`, `RETRIEVAL_WRONG_TARGET`,
`RETRIEVAL_INDEX_MISSING`, and `UNMEASURED_RETRIEVAL_SCOPE`.

## Boundary

Do not add aliases, rebuild an index, or infer that a missing search result
means missing knowledge until the structure and rendered paths have been
distinguished.

## Output

Write only `retrieval-auditor.json` with the probe matrix and the evidence for
each expected-to-observed mapping.
