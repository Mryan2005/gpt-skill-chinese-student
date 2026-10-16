# Check ephemeral workspace contract

Every check run owns one disposable workspace:

~~~text
<subject-project>/.check/current/
├─ findings.json
├─ audit-report.json
├─ snapshots/
├─ screenshots/
├─ render-cache/
├─ retrieval-cache/
├─ validator-output/
└─ subagent-reports/
~~~

## Reset order

~~~text
NEW_CHECK_REQUEST
→ CLEANUP_PREVIOUS_CHECK_RUN
→ WORKSPACE_VERIFIED_CLEAN
→ LOAD_CURRENT_CANONICAL_STATE
→ RUN_AUDITS
→ WRITE_FINDINGS
→ REPORT
→ CLOSED
~~~

Before loading the current Subject, delete the entire .check/current directory and recreate it. Do not delete individual guessed files.

Previous findings, audit reports, HTML snapshots, screenshots, render caches, retrieval results, validator output, debug files, intermediate statistics, subagent reports, and old check snapshots are disposable. The next audit must derive findings from the current canonical state, not from yesterday's report.

## Preserve boundary

The reset must not delete Source Layer, Derived Layer, canonical Markdown, Knowledge Network, learner_state, or the Subject manifest. check only reads those artifacts and writes the disposable audit result.

## Clean verification

The finding report records:

~~~text
workspace.root = .check/current
workspace.previousRunDeleted = true
workspace.cleanVerified = true
workspace.residualPaths = []
~~~

Any residual file blocks the audit with CHECK_WORKSPACE_NOT_CLEAN.
