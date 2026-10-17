# Patch proposal schema

Fixers analyze findings and write `fix.patch-proposal.v1` proposals. They do not
write canonical files directly.

~~~json
{
  "schemaVersion": "fix.patch-proposal.v1",
  "proposalId": "proposal-relation-001",
  "fixer": "relation-fixer",
  "findingIds": ["finding-019"],
  "action": "remap_endpoint",
  "confidence": "high",
  "evidence": [{"path": "derived/relations.json", "locator": "relations[19]"}],
  "filesAffected": ["derived/relations.json"],
  "mutationScope": "derived-relations",
  "operations": [{"op": "replace", "path": "relations[19].to", "value": "card:new-id"}],
  "decision": "PROPOSED",
  "sourceMutation": false
}
~~~

The orchestrator may change `decision` to `APPLY`, `REJECT`, or
`NEEDS_REVIEW`. Every operation must cite one or more check findings and keep
`sourceMutation=false`.
