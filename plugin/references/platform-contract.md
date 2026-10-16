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

## Ownership

- learn owns source intake, Subject routing, persistence, and the common output boundary;
- a domain model owns the structure and meaning of derived records;
- check audits source/derived separation without repairing it;
- exam reads a frozen derived state and exam source, then emits repair requests.
