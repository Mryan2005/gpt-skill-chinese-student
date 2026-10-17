# Provenance fix

Repair Derived `sourceIds`, locators, provenance labels, and broken internal
references when the check evidence identifies an unambiguous existing Source.
If no Source supports the repair, emit `BLOCKED_BY_SOURCE`. Do not invent a
quote or change the Source record.
