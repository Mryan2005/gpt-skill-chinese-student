# Retrieval audit

## Use this playbook when

The user cannot find a concept, question, chapter, or relation through search
and navigation.

## Dispatch

Run [retrieval-auditor](../agents/retrieval-auditor.md). Include the rendering
auditor when the real UI path is available, and include structure or relation
evidence when the merger needs to classify the root cause.

## Gate

A static matrix cannot claim that a real interaction was measured. Distinguish
zero hits, ambiguous hits, wrong mappings, missing indexes, and unmeasured
interaction scope.
