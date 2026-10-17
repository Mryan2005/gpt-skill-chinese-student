---
name: update
description: Use as the plugin and Subject schema migration front door when an existing Subject must move between plugin, content, domain, renderer, or artifact versions. Do not use for learning new material or adding ordinary content.
---

# 中式学生：迁移入口

update 是插件版本迁移器和 Content Schema Migration Runner。它不是 learn 的内容更新，也不是重新学习原始材料。

## Non-negotiables

- Source Layer 永远不因 Derived migration 改写。
- 只迁移 Derived、Subject metadata、artifact 和 progress schema。
- 每次迁移先 Detect/Plan，再 Snapshot，然后执行连续的小迁移。
- 每个 migration 必须有稳定 ID、前置版本、目标版本、owner 和 idempotent 声明。
- 无法确定性迁移时报告 NEEDS_REDERIVATION 或 BLOCKED_BY_SOURCE，不猜、不静默丢数据。
- 迁移后必须重建受影响 artifact，并调用 `check full-audit` 作为最终 Gate。
- SNAPSHOT_FROZEN 之后，update 不得影响正在进行的 exam。

平台版本合同见 [platform-contract.md](../../references/platform-contract.md)。迁移合同见 [update-contract.md](references/update-contract.md)、[migration-plan.md](references/migration-plan.md) 和 [change-impact.md](references/change-impact.md)。

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
| 识别 Subject 是否过期 | [detect.md](playbooks/detect.md) |
| 生成迁移计划和影响范围 | [plan.md](playbooks/plan.md) |
| 执行一个或多个连续 migration | [migrate.md](playbooks/migrate.md) |
| 重建 canonical Markdown/HTML/artifact | [rebuild.md](playbooks/rebuild.md) |
| 运行 check 并判断迁移是否成功 | [validate.md](playbooks/validate.md) |
| 汇总迁移结果和阻断项 | [report.md](playbooks/report.md) |

## Done gate

只有目标版本 metadata 已写入、Source hash/版本保持不变、Derived/artifact 迁移完成、
迁移可重复执行、`check full-audit` 返回 `PASS` 或 `PASS_WITH_WARNINGS`，并且所有
rederivation/source blockers 已列出时，才能报告迁移完成。
