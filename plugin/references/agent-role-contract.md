# Agent role contract

The plugin predefines **roles**, not permanent agents. A role is a stable
contract with scoped inputs, output, and mutation authority. Runtime capacity
only changes whether roles run in parallel, batched, or sequentially.

The machine-readable source of truth is
[agent-role-registry.v1.json](agent-role-registry.v1.json). The registry is
validated by `plugin/scripts/validate_agent_roles.py` and by the plugin-wide
structure validator.

## Shared rules

1. A non-merger role writes only its isolated report or Patch Proposal.
2. Every workflow has exactly one merger/coordinator role. It is the only role
   allowed to write that workflow's declared final output.
3. Isolated reports carry the run ID, input snapshot identity, role ID, and
   evidence references. A merger rejects stale or cross-run reports.
4. Roles may share immutable input but never a mutable canonical artifact.
   When a canonical write is necessary, the merger applies it serially.
5. Capacity failure changes execution mode, not required role coverage. The
   orchestrator runs remaining roles sequentially when no agent slot exists.
6. Re-running the same role/run pair must converge on the same report or
   proposal; idempotent merge and write gates remain the workflow authority.

## Workflow ownership

| Workflow | Isolated roles | Single merger/coordinator | Final write boundary |
| --- | --- | --- | --- |
| `learn` | intake, content, question, domain mapping | subject merger | canonical Subject after validators |
| `exam` | Hit inspection, independent answer, grading | exam coordinator | `.exam/current/` and frozen Exam Result only |
| `review` | material, learner, annotation, gap research | review merger | `.review/current/`; Learner State only via eligibility gate |
| `check` | specialized auditors | finding merger | `.check/current/` report only |
| `fix` | specialized Patch Proposals | fix orchestrator | allowed Derived/Runtime/Generated Artifact phases |

`exam` keeps the Hit Inspector separate from the Independent Answerer. The
answerer never receives graph/card/Hit/solution context. `review` consumes
frozen evidence and does not become a second exam or artifact repairer.
