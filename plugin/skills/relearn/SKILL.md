---
name: relearn
description: Use for an explicitly confirmed destructive rebuild of a Subject's Derived learning state from preserved Source records. Do not use for ordinary learning, Subject updates, schema migration, or deleting a Subject.
---

# Relearn

`relearn` discards a Subject's Derived learning state and rebuilds it from
preserved Source through `learn` and the domain model. It is not ordinary
learning and it is not `update`.

## Non-negotiables

- Identify the Subject and produce an impact report before deleting anything.
- Show the delete and preserve lists and wait for explicit confirmation.
- Delete only Derived data, artifacts, progress, indexes, and old render output.
- Preserve Source, Source Records, original questions, official answers,
  original explanations, and provenance.
- Create a one-time reset manifest before deletion. Apply deletion only with
  the explicit `--apply` step.
- Verify the Derived area is empty before calling `learn` and the domain model.
- Run `check` after rebuilding. A blocker or error prevents completion.
- `relearn` is not `reset-subject` and never deletes Source.

## State machine

~~~text
RELEARN_REQUESTED
→ IMPACT_ANALYZED
→ WAITING_FOR_USER_CONFIRMATION
→ CONFIRMED
→ DELETE_DERIVED_STATE
→ VERIFY_CLEAN
→ CALL_LEARN
→ LOAD_DOMAIN_MODEL
→ REBUILD
→ CHECK_FULL_AUDIT
→ RELEARN_COMPLETE
~~~

Stop at `WAITING_FOR_USER_CONFIRMATION` without explicit confirmation.

## Routing

- Impact analysis: [impact-analysis.md](playbooks/impact-analysis.md)
- Confirmation and reset: [confirm-and-reset.md](playbooks/confirm-and-reset.md)
- Rebuild: [rebuild.md](playbooks/rebuild.md)
- Validation: [validate.md](playbooks/validate.md)

## Done gate

Report `RELEARN_COMPLETE` only when the reset manifest is confirmed, Source is
unchanged, Derived is rebuilt, the current domain model is loaded,
`check full-audit` returns `PASS` or `PASS_WITH_WARNINGS`, and `learn` has
regenerated learner state. Report `RELEARN_WITH_ERRORS` for any blocker, error,
or blocked step.
