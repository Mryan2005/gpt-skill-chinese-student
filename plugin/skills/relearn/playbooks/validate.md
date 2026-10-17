# Validate

Run the relevant domain validators and then run `chinese-student: check full-audit` against the
rebuilt canonical state. Report Source preservation, Derived counts, provenance
coverage, the check result, findings, blockers, and the final
RELEARN_COMPLETE or RELEARN_WITH_ERRORS status. Do not repair during this
validation pass. A check result of `FAIL` or `BLOCKED` prevents
RELEARN_COMPLETE.
