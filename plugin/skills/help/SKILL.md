---
name: help
description: Use to show the read-only Chinese Student command reference, route boundaries, subcommands, inputs, outputs, and safety gates. It never invokes another workflow.
---

# Help

`help` is the read-only command reference for the Chinese Student plugin. It
does not invoke another Skill, modify Source, Derived content, Exam Result,
Generated Artifacts, or Learner State.

## Calls

```text
$chinese-student:help
$chinese-student:help <command>
$chinese-student:help <command> <subcommand>
$chinese-student:help all
```

Use the live Skill folders, the verified help index in
[command-index.json](references/command-index.json), and the machine-readable
ownership/routing contract at
`../../references/skill-registry.v1.json`. The route contract is validated
before help is rendered, so stale commands, missing Skills, mismatched kinds,
and direct domain-model routes fail visibly. `study-math`, `study-politics`,
and `study-exam-oriented-english` are loaded by `learn`, not ordinary user
workflows. The human-readable routing boundary is documented in
[command-routing.md](../../references/command-routing.md).

Natural-language routing can be checked without executing a workflow:

```powershell
python -X utf8 plugin/scripts/route_command.py "考后复盘这套试卷"
```

The router returns a canonical namespaced invocation, an optional subcommand,
the selected domain model, and competing candidates when clarification is
needed. It never reads or writes a Subject.

Unknown commands must produce an error and an optional spelling suggestion;
they must never execute the suggested command.
