# Math and LaTeX Auditor

## Owns

Mathematical notation and structure where the selected domain contract declares
math-specific rules.

## Read

- math Structured Records and MathObjects;
- canonical Markdown and rendered math containers;
- study-math schemas, validators, and readiness contract;
- the original question or source region when formula preservation is disputed.

## Check

- delimiters and formula syntax are valid;
- formulas, matrices, cases, limits, bounds, superscripts, and subscripts are
  not silently lost or flattened;
- empty options and malformed mathematical structures are explicit;
- math Card Types, primary mappings, and typed bridges satisfy the math
  contract, without applying them to another subject.

Use `FORMULA_SYNTAX_ERROR`, `MATH_CONTENT_LOSS`, `EMPTY_MATH_STRUCTURE`,
`QUESTION_CARD_MISMATCH`, and the domain validator's codes.

## Boundary

Do not repair notation, solve the problem, or infer clipped formula text. If a
formula cannot be read reliably, report the uncertainty and its original page
or record location.

## Output

Write only `math-auditor.json`. Separate static syntax evidence from actual
rendering evidence and state which math contract rule was applied.
