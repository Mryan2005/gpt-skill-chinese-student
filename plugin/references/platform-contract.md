# Platform data contract

This contract applies to every Subject and every domain model in the plugin.

## Source and Derived are separate namespaces

The platform stores two logical layers:

~~~text
sources
  original documents, images, quotes, questions, official answers, annotations

derived
  cards, concepts, principles, summaries, relations, question mappings, recall prompts
~~~

Source content is immutable with respect to derived learning content. Derived content may be deleted, split, re-extracted, or rebuilt without changing the source.

## Source Independence Principle

1. Original source and derived learning content are different entities.
2. Extraction, summary, rewrite, explanation, and classification never modify a source.
3. Deleting derived content never deletes a source.
4. Rebuilding derived content never overwrites a source.
5. A source changes only because the user replaces it, supplies a new version, or confirms an explicit source correction.
6. Every derived record has provenance that points to one or more source records and locators.
7. A conflict keeps the source unchanged and marks the derived record as conflict or needs-review.
8. Do not rewrite a source to make a card read more smoothly.

## Versioning

Keep source and derived versions independent:

~~~text
source_version = 1
derived_version = 7
~~~

Rebuilding cards increments derived_version. It does not increment source_version.

## Minimum record shapes

~~~json
{
  "source": {
    "id": "src-book-p42-p3",
    "entityType": "source_text",
    "text": "原始可读文字",
    "locator": {"path": "book.pdf", "page": 42},
    "sourceVersion": 1,
    "status": "COMPLETE"
  },
  "derived": {
    "id": "derived-card-001",
    "type": "domain_defined_type",
    "title": "派生内容",
    "sourceRefs": [
      {"sourceId": "src-book-p42-p3", "locator": "paragraph-3"}
    ],
    "derivedVersion": 7,
    "status": "ACTIVE"
  }
}
~~~

Domain models may add fields, but they must preserve source references and must not collapse the two layers into one mutable text field.

## Answer and solution provenance

Question-derived results are separate from source answers and solutions:

~~~text
official_answer / official_solution
historical_answer / historical_solution
derived_answer / derived_solution
~~~

If the original question is complete enough, a domain model may independently solve it and store derived_answer and derived_solution. The derived result must carry provenance, confidence or needs-review state, and the derivation must remain separate from the Source layer.

If a key condition, formula, option, figure, or sub-question is missing, do not generate a conclusion. Preserve the question gap and leave derived_answer and derived_solution empty. A conflict between official, historical, and derived results is reported, never resolved by overwriting one result.

## Subject migration metadata

Every persisted Subject should expose the versions required by update:

~~~json
{
  "subjectId": "math-1",
  "pluginVersion": "0.3.0",
  "contentSchemaVersion": 2,
  "domain": "math",
  "domainSchemaVersion": 2,
  "rendererVersion": 2,
  "sourceVersion": 1,
  "derivedVersion": 8
}
~~~

update compares these values with the current contracts. It migrates Derived and artifacts in small idempotent steps, keeps Source unchanged, and runs check before declaring success.

An exam snapshot records migrationStatus=UP_TO_DATE. Once SNAPSHOT_FROZEN, no update may alter that snapshot or its measured Derived state.

## Ownership

- learn owns source intake, Subject routing, persistence, and the common output boundary;
- a domain model owns the structure and meaning of derived records;
- check audits source/derived separation without repairing it;
- exam reads a frozen derived state and exam source, then emits repair requests.
