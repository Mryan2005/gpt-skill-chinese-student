# Schema and identity fix

Repair deterministic, schema-compatible Derived fields, generated IDs, stale
caches, broken field names, and duplicate generated records when the check
finding supplies an unambiguous operation. Escalate migration work to
`REQUIRES_UPDATE` and semantic identity choices to a proposal requiring review.

Never modify Source or silently delete an ambiguous entity.
