# Apply optimization

1. Load a report produced from the current artifact fingerprint.
2. Require explicit authorization. Refuse stale plans, missing evidence,
   answer-only repairs, and any operation without a complete migration record.
3. Apply only safe referential migrations, such as an exact-duplicate alias.
   Semantic merge, split, and deletion operations remain blocked unless their
   explicit domain migration is present and the user confirmed the risk.
4. Validate relation endpoints, question mappings, aliases, preservation of
   Source/Exam Result/Learner State, and the idempotent re-analysis result.
