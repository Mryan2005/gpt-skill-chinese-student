# Relation integrity

## Use this playbook when

Use it when relations are dangling, untyped, undirected, vague, duplicated, or inconsistent with a domain model.

## Procedure

1. Check every from and to ID against the current Subject records.
2. Check relation type, direction, reason, provenance, and duplicate edges.
3. Check hierarchy separately from semantic relations.
4. Check domain-specific bridge requirements, such as mathematical outgoing relations.
5. Emit findings with repairOwner learn/relation-structure or the domain model.

## Gate

The audit reports the relation and its first invalid endpoint or missing semantic field. It does not edit or delete an edge.
