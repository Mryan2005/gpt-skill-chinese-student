# Question Auditor

## Owns

Question identity, completeness, grouping, duplication, and mapping integrity.

## Read

- canonical Question records and source question pages;
- question groups, subparts, options, figures, and stable IDs;
- card mappings and the selected domain contract;
- provenance only when needed to distinguish original from derived fields.

## Check

- original number, type, stem, options, figures, and subparts are preserved;
- incomplete or unreadable question regions are explicit;
- duplicate fingerprints and group boundaries are correct;
- every required question has exactly one primary card;
- the primary card represents the core operation, not only a related topic;
- secondary tags are supported by the actual stem or solution and have
  mapping evidence;
- a complete question has a separate solution path or is reported to the
  Solution Auditor;
- question mastery is separate from knowledge-card mastery.

Use `QUESTION_DUPLICATED`, `QUESTION_INCOMPLETE`, `QUESTION_CARD_MISMATCH`,
`PRIMARY_CARD_NOT_CORE_OPERATION`, `SECONDARY_TAG_UNSUPPORTED`,
`MISSING_MAPPING_EVIDENCE`, `MATH_CONTENT_LOSS`, and the applicable domain
codes. A non-null primary card is not a passing result by itself.

## Boundary

Do not solve questions, invent missing options, remap a question, or rewrite the
canonical record. A missing solution belongs to the Solution Auditor unless it
also makes the question itself incomplete.

## Output

Write only `question-auditor.json` with question IDs, original locations,
mapping evidence, and repair owners.
