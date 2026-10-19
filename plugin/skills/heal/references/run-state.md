# Heal run state

The disposable workspace is:

~~~text
.heal/
└── current/
    ├── round-<n>/
    │   ├── learner/
    │   │   ├── trace.jsonl
    │   │   ├── friction.json
    │   │   └── summary.json
    │   └── maintainer/
    │       ├── evaluation.json
    │       ├── repair-plan.json
    │       └── repair-report.json
    └── state/
        ├── round-state.json
        ├── optimize-report.json
        └── heal-report.json
~~~

Reset the entire `.heal/current/` directory before a new run. Do not delete
Source, Derived, canonical learner state, or `.local/learner/` while resetting.

Every round must record:

- a fresh novice context ID and user-facing artifact version;
- the learning trace and friction fingerprints;
- understanding coverage, dead ends, and friction counts;
- each Maintainer decision and its evidence;
- repair changes, source-mutation flags, and local validation;
- the non-consuming `checkBefore` and `checkAfter` gates;
- exactly one `optimizationRunCount` and its actions, including a recorded
  `NO_OP` and any stability-gate result;
- whether synthetic data stayed inside the heal workspace.

Previous round traces are comparison data only. The next Novice must not read
them. The Maintainer may read them to compare progress, but it must evaluate
the current trace against the current artifact before writing.
