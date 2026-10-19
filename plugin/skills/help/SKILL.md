---
name: help
description: Read-only command reference for Chinese Student skills, subcommands, inputs, outputs, side effects, and safety boundaries.
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

Use the live Skill folders plus the verified command index in
[command-index.json](references/command-index.json). `study-math` and
`study-politics` are reported as Domain Models loaded by `learn`, not as
ordinary user workflows.

Unknown commands must produce an error and an optional spelling suggestion;
they must never execute the suggested command.
