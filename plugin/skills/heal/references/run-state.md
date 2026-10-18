# Heal run state

The disposable workspace is:

~~~text
.heal/
└── current/
    ├── checker/
    │   └── check-<round>.json
    ├── fixer/
    │   └── fix-<round>.json
    └── state/
        ├── round-state.json
        └── heal-report.json
~~~

Reset the entire `.heal/current/` directory before a new run. Do not delete
Source, Derived, canonical learner state, or `.local/learner/` while resetting.

The orchestrator writes one current round state at a time. The reusable Checker
and Fixer may retain role context, but they must reload the current artifact and
the current report at every handoff. Previous round files are comparison data,
not permission to reuse stale findings.

Every final report must include:

- initial and final severity counts;
- each round's check/fix IDs and artifact hashes;
- finding fingerprints and resolved/persisted/new/regressed counts;
- Checker read-only and Fixer write-scope declarations;
- local validation status;
- final check result and exact stop reason.
