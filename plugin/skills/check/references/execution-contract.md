# Check execution contract

Auditor roles are contracts. Agent threads are execution resources. A role must
run even when no new agent thread is available.

## Level 0 validators

Run deterministic validators before semantic workers:

- duplicate entity IDs;
- missing or multiple primary-card mappings;
- metadata in the Question Bank;
- missing relation type, direction, or reason;
- missing provenance or broken source IDs;
- `SOLUTION_PENDING` counts and status contradictions;
- LaTeX delimiter and basic command syntax;
- HTML structure and required navigation hooks.

These checks do not consume agent capacity. Their findings use the same Finding
Schema as semantic audits.

## Auditor bundles

The scheduler assigns roles to worker bundles. A bundle is a work plan, not a
required agent thread.

| Bundle | Roles |
| --- | --- |
| `structure` | structure, source, provenance, question |
| `domain` | content, solution, math, relation |
| `presentation` | latex, rendering, retrieval |
| `coverage` | coverage, readiness |

The question role checks identity and storage integrity. Domain auditors check
the semantic meaning of mappings and solutions. The merger removes overlap.

## Capacity ladder

Use the first mode that the current capacity supports:

| Capacity | Execution mode | Plan |
| --- | --- | --- |
| three or more slots | `parallel-agent` | run up to three bundles in parallel, then drain the remaining bundle |
| two slots | `batched-agent` | run two bundles, then the other two |
| one slot | `shared-agent` | one existing worker runs all bundles in sequence |
| zero slots | `orchestrator-fallback` | the check orchestrator runs every bundle and role in sequence |

The default maximum parallelism is three. The scheduler may use a lower value
when the host reports fewer slots.

## Spawn failure policy

Count consecutive failures to create a new agent thread. After two failures:

1. emit `AGENT_CAPACITY_DEGRADED` as execution metadata;
2. stop creating new agent threads for this run;
3. move every remaining role to a shared worker or the orchestrator;
4. continue until every required role is completed or a real input blocker is
   found.

An agent capacity failure never makes an auditor `skipped`. Only a missing,
unreadable, or invalid required artifact may produce `auditStatus=BLOCKED`.

## Report fields

The final report separates audit result from execution method:

~~~json
{
  "execution": {
    "requestedMode": "multi-agent",
    "actualMode": "batched-agent",
    "maxParallel": 2,
    "maxConsecutiveSpawnFailures": 2,
    "spawnFailures": 0,
    "spawningDisabled": false,
    "fallbackReason": null
  },
  "auditor": {
    "auditor": "math",
    "auditStatus": "PASS",
    "executionMode": "shared-agent",
    "workerBundle": "domain"
  }
}
~~~

`auditStatus` is `PASS`, `WARNING`, `FAIL`, or `BLOCKED`. `executionMode` is
`parallel-agent`, `batched-agent`, `shared-agent`, or
`orchestrator-fallback`. A fallback execution can still produce `PASS`.
