# Repair plan schema

The orchestrator writes a `fix.repair-plan.v1` before applying any mutation.

~~~json
{
  "schemaVersion": "fix.repair-plan.v1",
  "fixRunId": "math-one-fix-001",
  "basedOnCheck": {
    "checkRunId": "math-one-check-001",
    "artifactVersion": "math-records.v1",
    "artifactHash": "sha256:current",
    "schemaVersion": "check.finding.v1"
  },
  "phases": [
    {
      "phaseId": "schema",
      "order": 1,
      "kind": "deterministic",
      "findingIds": ["finding-001"],
      "dependsOn": [],
      "mutationScope": ["derived-schema"],
      "status": "planned"
    }
  ]
}
~~~

Every phase names its findings, dependencies, mutation scope, and kind. A plan
with a Source mutation or a hidden destructive operation is invalid.
