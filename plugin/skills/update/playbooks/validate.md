# Validate

Run domain validators, markup checks, artifact checks, and `chinese-student: check full-audit`.
Any `FAIL` or `BLOCKED` check result produces `MIGRATED_WITH_ERRORS`. A missing
source or unresolved domain judgment remains an explicit blocker. Do not let
update repair a check finding during the same validation pass.
