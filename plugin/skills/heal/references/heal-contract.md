# Heal contract

`heal` is a bounded orchestration layer over `check` and `fix`.

## Round contract

One repair round is:

~~~text
CHECK(n) against current canonical and generated state
→ evaluate findings and stop conditions
→ FIX(n) using only CHECK(n)'s fresh report
→ local validation
→ compare fingerprints and artifact hashes
~~~

The next check must reload current Source, Derived, Learner Model, and generated
artifacts. A previous report may be used only to calculate `resolved`,
`persisted`, `new`, and `regressed`; it is never a substitute for current
evidence.

`fix(n).basedOnCheckRound` must equal `n`, and
`fix(n).artifactHashBefore` must equal the artifact hash checked by `check(n)`.
The Fixer must not consume an older report after a new check has completed.

## Role boundary

| Role | Permission | Responsibility |
| --- | --- | --- |
| Checker | read-only | invoke existing check playbooks, validators, and domain contracts; produce current findings |
| Fixer | write-enabled | consume current findings and existing fix contract; produce repair report and local validation |
| Heal orchestrator | coordinates | reset workspace, sequence roles, compare progress, enforce stop conditions, write heal report |

The Checker cannot edit to make its own findings disappear. The Fixer cannot
declare the artifact clean. Only a later Checker result can satisfy the quality
gate.

## Bounds and stop conditions

- `MAX_ROUNDS = 10`. After the tenth fix, run `FINAL_CHECK` and stop.
- Stop on `PASS`.
- Stop on `PASS_WITH_WARNINGS` when blocker and error counts are zero and no
  auto-fixable error or blocker remains.
- Stop on an unfixable source blocker, unparsable artifact, unsafe state, or
  required authentication/input that the current run cannot provide.
- Stop and report `RELEARN_REQUIRED` when safe local repair would require
  deleting and rebuilding Derived state. Do not bypass relearn confirmation.
- Stop and report `UPDATE_REQUIRED` when the defect is a schema/plugin migration
  rather than a repair. Do not copy migration logic into heal.
- Stop after two consecutive rounds with no meaningful finding elimination.
- Stop when repair repeatedly recreates the same findings or introduces
  unacceptable regressions.

Warnings are not automatically defects. A warning may remain in a successful
`PASS_WITH_WARNINGS` result when the stronger gates are clean.

## Progress comparison

Use the stable finding fingerprint:

~~~text
code + entityId + rootLayer
~~~

For each round report:

~~~json
{
  "resolved": 80,
  "persisted": 20,
  "new": 79,
  "regressed": 12
}
~~~

`resolved` means a prior fingerprint is absent from the next fresh report.
`new` means a current fingerprint was absent from the prior report.
`regressed` records a previously clean or resolved entity that now fails again.
Do not call a run healthy merely because the total count fell by one.

## Escalation boundary

The following are terminal unless the current Source or authorized external
input makes them safe to resolve: missing/corrupted Source, unreadable required
question material, ambiguous official answers, required PDFs that are absent,
authentication gates, unsafe or unparsable artifacts. Record the concrete
evidence and stop; do not infer or fabricate missing content.

`heal` may read and preserve fix reports, but its final report must record the
current artifact hash, all round identities, the final check, and the exact
reason it stopped.
