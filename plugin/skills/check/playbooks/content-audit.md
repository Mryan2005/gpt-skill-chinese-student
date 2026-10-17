# Content audit

## Use this playbook when

The user asks whether the cards contain enough clear, domain-correct learning
content rather than only whether the files exist.

## Dispatch

Run [content-auditor](../agents/content-auditor.md) with the selected domain
contract. Add [coverage-auditor](../agents/coverage-auditor.md) when the issue
also asks whether source topics were represented, and add the domain auditor
when semantic correctness is in scope.

## Gate

Report missing conditions, boundaries, distinctions, operations, and recall
content with evidence. Do not treat card length, HTML existence, or mastery
state as proof of content sufficiency.
