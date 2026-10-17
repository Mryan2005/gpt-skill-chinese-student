# LaTeX Auditor

## Owns

Syntax and source-preservation checks for mathematical notation. It does not
own mathematical meaning or the study-math Card Schema.

## Read

- original formula or MathObject records;
- canonical Markdown and generated formula containers;
- the applicable markup validator and renderer diagnostics;
- page or record locators when a formula was transformed.

## Check

Run two separate checks:

1. Syntax: delimiters, command arguments, environment pairs, illegal commands,
   and malformed formula containers.
2. Preservation: compare formula structure and required bounds, indices,
   matrices, cases, superscripts, and subscripts with the source record.

Use `LATEX_SYNTAX_ERROR`, `MATH_CONTENT_LOSS`, and
`FORMULA_SOURCE_MISMATCH`. A formula that renders successfully can still fail
the preservation check.

## Boundary

Do not repair notation, infer clipped source text, or decide whether a theorem
is mathematically valid. Send semantic questions to the Math Auditor.

## Output

Write only `latex-auditor.json`. Mark evidence as `syntax`, `rendered`, or
`source-comparison` so the merger does not confuse the checks.
