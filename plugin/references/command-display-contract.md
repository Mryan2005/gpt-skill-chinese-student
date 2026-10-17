# Command Display Contract

The plugin's internal Skill IDs and directories remain short and stable:

~~~text
learn
check
fix
sort
exam
update
relearn
profile
~~~

Every user-facing command uses the `chinese-student:` namespace.

## Display forms

~~~text
chinese-student: learn
chinese-student: check
chinese-student: fix
chinese-student: sort
chinese-student: exam
chinese-student: update
chinese-student: relearn
chinese-student: profile
~~~

Arguments keep the prefix:

~~~text
chinese-student: learn math
chinese-student: check questions
chinese-student: check latex
chinese-student: check full-audit
chinese-student: sort math
chinese-student: sort --errors
chinese-student: sort --review
chinese-student: profile math
chinese-student: relearn math
~~~

## Hard rules

- All user-facing Chinese Student commands must use the `chinese-student:`
  prefix.
- Internal Skill IDs may remain unprefixed in manifests, directories, routing
  tables, and implementation references.
- Do not rename Skill directories for display purposes.
- Documentation, help text, command suggestions, examples, status messages,
  onboarding text, and generated usage instructions use the namespaced form.
- Never suggest a bare `learn`, `check`, `fix`, `sort`, `exam`, `update`,
  `relearn`, or `profile` as this plugin's user-facing command.
- The namespace is a display identity. It does not have to match a physical
  directory name.
