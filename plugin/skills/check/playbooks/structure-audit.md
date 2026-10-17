# Structure audit

## Use this playbook when

Cards, nodes, modules, hierarchy, card size, domain fields, or progress
mappings look wrong.

## Dispatch

Run [structure-auditor](../agents/structure-auditor.md) and
[coverage-auditor](../agents/coverage-auditor.md). If the Subject is math, also
run [math-auditor](../agents/math-auditor.md) against the study-math contract.

## Gate

Use the selected domain's own card and coverage schema. Do not report a
mathematical Card Type as an error in a non-math Subject, and do not repair a
card while measuring it.
