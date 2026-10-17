# Coverage audit

## Use this playbook when

The user asks whether supplied material has been fully represented in the
knowledge graph, or which source concepts remain missing or partial.

## Procedure

1. Reset and freeze the current Subject before measuring coverage.
2. Run [coverage-auditor](../agents/coverage-auditor.md) with the domain's
   expected-content contract.
3. Use the Finding Merger for overlaps with source, structure, or provenance
   findings.
4. Report the coverage matrix and every `missing`, `partial`, `duplicate`, or
   `uncertain` row.

## Gate

Coverage is not mastery and a page count is not evidence of coverage. Do not
create cards or infer that a broad summary covers details that have no trace.
