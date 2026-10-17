# Relation audit

## Use this playbook when

Relations are dangling, untyped, undirected, vague, duplicated, or inconsistent
with the selected domain model.

## Dispatch

Run [relation-auditor](../agents/relation-auditor.md) and the applicable domain
contract. If the relation is only visible through the page, include the
[rendering auditor](../agents/rendering-auditor.md).

## Gate

Report both endpoints, the first invalid field, and the relation rule. Do not
add, delete, or retarget an edge.
