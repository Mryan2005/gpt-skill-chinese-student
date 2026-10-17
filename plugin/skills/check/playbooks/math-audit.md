# Math audit

## Use this playbook when

The user asks about mathematical formulas, LaTeX, matrices, limits, options,
math Card Types, or mathematical question mappings.

## Dispatch

Run [math-auditor](../agents/math-auditor.md) with the study-math schema and
validators. Add question or rendering auditors when the issue crosses those
boundaries.

## Gate

Math rules come from study-math. Check reports whether the artifact satisfies
that contract; it does not invent a new math taxonomy or repair a formula.
