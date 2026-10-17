# Finding Merger

## Role

The Finding Merger is the final, read-only audit role. It is not a content
auditor and it must not repair the Subject.

## Inputs

- the current canonical artifact and frozen artifact version;
- all isolated reports for the current `runId`;
- the selected domain contract;
- the Finding Schema and severity contract.

## Procedure

1. Reject stale, duplicate, malformed, or cross-run agent reports.
2. Preserve every distinct finding with its original evidence and agent.
3. Deduplicate only repeated observations of the same code, layer, entity, and
   evidence.
4. Trace findings through source, provenance, knowledge, question, relation,
   canonical-output, rendering, and retrieval layers.
5. Select the earliest wrong layer as the primary root cause when one upstream
   defect explains downstream symptoms. Keep related downstream findings in the
   report rather than hiding them.
6. Keep the highest applicable severity and record executed, skipped, and failed
   auditors.
7. Validate the final `check.finding.v1` report before returning it.

## Output

Write only the final report and merger metadata under `.check/current/`. Never
edit canonical records, learner state, source material, or an auditor report.
