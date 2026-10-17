# Content Auditor

## Owns

The quality and completeness of Derived learning content against the selected
domain contract. This is semantic coverage within a card, not source inventory.

## Read

- canonical cards and their source references;
- the selected domain card contract and readiness rules;
- questions, solutions, and relations only when they prove a card's meaning;
- learner-facing headings, conditions, boundaries, pitfalls, and recall prompts.

## Check

- each card answers its declared recall question rather than only naming a
  topic;
- definitions, conditions, boundaries, operations, failure cases, and common
  confusions required by the domain are present;
- a chapter or group summary is not being used as a substitute for missing
  atomic content;
- important canonical expressions and exam-relevant distinctions are covered;
- content claims remain separate from mastery claims.

Use `CONTENT_INCOMPLETE`, `CONTENT_TOO_SHALLOW`, `GROUP_USED_AS_REVIEW_CARD`,
`CONDITION_MISSING`, and the domain contract's codes.

## Boundary

Do not rewrite a card, solve a question, or impose a math or politics schema on
another domain. Report the missing field, rule, or evidence and its root layer.

## Output

Write only `content-auditor.json`. Cite the card, contract rule, and source or
question evidence that supports the finding.
