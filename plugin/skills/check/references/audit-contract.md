# Audit contract

`check` is a read-only verification system. It runs deterministic validators and
semantic auditor roles against the current canonical Subject, then uses one
merger to produce the final report. Auditor roles do not require one agent
thread each. See [execution-contract.md](execution-contract.md).

## Execution model

1. Reset `.check/current/` and verify that it is empty.
2. Freeze one canonical artifact version and one check `runId`.
3. Run deterministic validators without consuming agent capacity.
4. Plan the required auditor queue and choose parallel, batched, shared-worker,
   or orchestrator-fallback execution from current capacity.
5. Give every auditor the same frozen artifact, domain contract, and run ID.
6. Allow each auditor to write only its own report under
   `.check/current/subagent-reports/`. Auditors must not write canonical content,
   learner state, HTML, or another auditor's report.
7. Run the Finding Merger after every required auditor has completed or a real
   input blocker has been recorded. Agent spawn failure is not an audit skip.
8. Validate the merged `check.finding.v1` report and return the result without
   repairing the Subject.

## Auditor boundary

Every auditor must declare:

- `agentId` and the root layer it owns;
- the exact input paths and domain contract it inspected;
- checks executed, skipped, and their reason;
- evidence locations for every finding;
- an audit status: `PASS`, `WARNING`, `FAIL`, or `BLOCKED`;
- an execution mode: `parallel-agent`, `batched-agent`, `shared-agent`, or
  `orchestrator-fallback`.

An auditor may parse, search, render, probe, and validate. It may not fix,
reclassify, delete, overwrite, or silently infer missing source material.

## Finding Merger

The merger accepts only reports for the current `runId` and current artifact
version. It must:

- reject stale, duplicate, or cross-run reports;
- preserve distinct findings even when they mention the same entity;
- deduplicate repeated observations using code, rootLayer, entity, and evidence;
- trace dependencies to the earliest wrong rootLayer;
- select one primary root cause when a single upstream defect explains downstream
  findings, while retaining the downstream findings as related evidence;
- preserve the highest applicable severity;
- record executed auditors, blocked auditors, execution modes, and any real
  input reason that prevented a check.

For example, lost formula source evidence is one upstream blocker. A question
answer mismatch, an empty solution, and a rendering failure may be related
findings, but the merger must point repair to the source or classification rootLayer
when that is where the loss first occurred.

The merger reports root causes; it does not repair them.

## Modes

| Mode | Auditors |
| --- | --- |
| `full-audit` | all specialized auditors, then readiness aggregation |
| `source-audit` | source and provenance auditors |
| `structure-audit` | structure, content, coverage, and applicable domain auditors |
| `content-audit` | content and coverage auditors, plus the applicable domain auditor |
| `question-audit` | question, solution, provenance, and applicable math auditors |
| `latex-audit` | LaTeX auditor, plus math or rendering auditors when needed |
| `relation-audit` | relation auditor and applicable domain checks |
| `rendering-audit` | rendering auditor, with retrieval probes when requested |
| `retrieval-audit` | retrieval auditor |
| `readiness-audit` | all auditors required by the Subject's readiness contract |

The mode changes scope, not the read-only or evidence requirements.
