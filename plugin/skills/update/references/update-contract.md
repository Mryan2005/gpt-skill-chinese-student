# Update contract

## Scope

update handles plugin, content schema, domain schema, renderer, artifact, and progress migrations for existing Subjects. learn handles new learning material and ordinary content updates.

## Version sources

Read the Subject manifest before migration:

~~~json
{
  "subjectId": "math-1",
  "pluginVersion": "0.2.0",
  "contentSchemaVersion": 1,
  "domain": "math",
  "domainSchemaVersion": 1,
  "rendererVersion": 1,
  "sourceVersion": 1,
  "derivedVersion": 7
}
~~~

Compare it with the current plugin and domain contract. Do not infer age from HTML appearance.

## Migration outcomes

~~~text
UP_TO_DATE
MIGRATION_REQUIRED
INCOMPATIBLE
UNKNOWN_LEGACY
NEEDS_REDERIVATION
BLOCKED_BY_SOURCE
MIGRATED_WITH_ERRORS
~~~

## Rules

- Source content, source files, source hashes, original questions, official answers, and annotations are immutable during Derived migration.
- Migrations are ordered, small, named, idempotent, and auditable.
- A migration may transform only the fields declared by its contract.
- Domain migrations delegate interpretation to study-math, study-politics, or another domain model.
- A migration that needs absent source evidence stops with BLOCKED_BY_SOURCE.
- A migration that needs domain judgment stops with NEEDS_REDERIVATION and creates a repair request.
- Re-running a completed migration must produce UP_TO_DATE and no additional changes.
- check is the final validation owner. update does not mark success from its own self-report.
