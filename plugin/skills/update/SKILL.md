---
name: update
description: Use only to migrate an existing plugin, Subject, schema, renderer, or artifact version. Do not use for new learning, ordinary content updates, repairs, review, or destructive rebuilds.
---

# Update

`update` is the plugin and content-schema migration runner. It is not ordinary
learning and it is not a rebuild of the original material.

## Non-negotiables

- Never rewrite the Source Layer during a Derived migration.
- Migrate only Derived data, Subject metadata, artifacts, and progress schemas.
- Detect and plan before taking a snapshot or applying a migration.
- Give every migration a stable ID, source version, target version, owner, and
  idempotence declaration.
- If deterministic migration is impossible, report `NEEDS_REDERIVATION` or
  `BLOCKED_BY_SOURCE`. Do not guess or discard data silently.
- Rebuild affected artifacts and run `check full-audit` as the final gate.
- Do not affect an exam after `SNAPSHOT_FROZEN`.

Read [platform-contract.md](../../references/platform-contract.md),
[update-contract.md](references/update-contract.md),
[migration-plan.md](references/migration-plan.md), and
[change-impact.md](references/change-impact.md).

## State machine

~~~text
DETECT
  ↓
PLAN
  ↓
SNAPSHOT
  ↓
MIGRATE
  ↓
REBUILD
  ↓
VALIDATE
  ↓
REPORT
~~~

## Routing

| Goal | Playbook |
| --- | --- |
| Detect an outdated Subject | [detect.md](playbooks/detect.md) |
| Create a migration plan and impact report | [plan.md](playbooks/plan.md) |
| Apply one or more migrations | [migrate.md](playbooks/migrate.md) |
| Rebuild canonical Markdown, HTML, or artifacts | [rebuild.md](playbooks/rebuild.md) |
| Run `check` and validate the migration | [validate.md](playbooks/validate.md) |
| Summarize migration results and blockers | [report.md](playbooks/report.md) |

## Done gate

Report completion only when target metadata is written, Source hash and version
are unchanged, Derived artifacts are migrated, the migration is repeatable,
`check full-audit` returns `PASS` or `PASS_WITH_WARNINGS`, and every
rederivation or Source blocker is listed.
