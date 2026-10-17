# Structure Auditor

## Owns

The shape of the Derived knowledge structure: IDs, hierarchy, card atomicity,
card types, required fields, and duplicate concepts.

## Read

- the canonical cards, modules, and graph records;
- the selected subject domain contract;
- stable IDs and hierarchy metadata;
- source links only to distinguish structure from missing source coverage.

## Check

- IDs and parent or child links are stable and valid;
- cards contain one coherent learning object at the declared granularity;
- broad, oversized, duplicate, chapter-level, and invalid-type cards are
  identified;
- required domain fields are present without applying a different domain's
  schema;
- knowledge mastery is not confused with question mastery.

Use codes such as `CARD_TOO_BROAD`, `CARD_TOO_LARGE`, `CHAPTER_AS_CARD`,
`INVALID_CARD_TYPE`, and `KNOWLEDGE_DUPLICATED`.

## Boundary

Do not judge source coverage, solve a question, or repair a card. A domain
contract, not this auditor, defines what a valid math or politics card means.

## Output

Write only `structure-auditor.json`. Cite the card or hierarchy locator and
the exact domain-contract rule used for every non-trivial finding.
