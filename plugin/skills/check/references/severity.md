# Finding severity

## blocker

The Subject cannot be trusted or used for its stated purpose. Examples include metadata in Question Bank, missing primary mappings across a required set, lost question formulas, broken canonical output, or a failed exam-readiness dependency.

## error

A concrete correctness or integrity defect that invalidates the affected entity or path. Examples include a duplicate Question ID, a dangling relation, a wrong typed edge, or a solution mismatch.

## warning

A risk or incomplete check that does not invalidate the whole Subject but requires attention. Examples include an unresolved alias, an unmeasured interaction count, or a source boundary that is explicit but incomplete.

## info

An observed fact, successful check, or scope limitation that does not indicate a defect.

Severity is assigned by impact on the requested goal, not by how easy the repair is. A warning must not be used to hide a blocker.
