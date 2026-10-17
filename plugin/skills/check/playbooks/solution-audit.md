# Solution audit

## Use this playbook when

The user asks whether answers, solutions, and their official, historical, or
AI-derived provenance are trustworthy.

## Dispatch

Run [solution-auditor](../agents/solution-auditor.md),
[provenance-auditor](../agents/provenance-auditor.md), and the applicable domain
auditor. The merger must keep conflicts visible and identify the earliest
source or classification defect.

## Gate

An absent official solution is not a failed derived-solution attempt by itself.
An AI-derived answer may be reported only as derived, never as official or
historical. A question with missing key conditions cannot receive a fabricated
conclusion.
