# Chinese Student

Chinese Student is an open-source Agent Plugin for local learning materials.
It turns textbooks, images, exam papers, and explanations into traceable subject
knowledge graphs for later retrieval and closed-book assessment.

The repository contains the plugin source, the mathematics domain model,
structured record schemas, reusable playbooks, and deterministic validators. It
does not contain a user's private study materials.

The project is provided by Mryan2005.

## License

Chinese Student is released under the [GNU Affero General Public License v3.0 or later](LICENSE).

## Design influence

The project follows the layered skill structure and engineering discipline used
by [pstack](https://github.com/cursor/plugins/tree/main/pstack): keep front
doors small, route work to focused playbooks, encode repeated lessons in
schemas and validators, and verify the real artifact before reporting success.

## Core skills

| Skill | Purpose |
| --- | --- |
| `learn` | Cross-subject learning workflow. Ingests sources, builds cards and relations, and maintains the canonical Markdown and knowledge graph. |
| `update` | Version migration runner for existing Subjects, schemas, artifacts, and progress. It does not modify Source. |
| `relearn` | Confirmed destructive rebuild. It removes Derived state, preserves Source, and rebuilds through `learn` and the domain model. |
| `study-math` | Mathematics domain model for card types, question records, formula integrity, typed relations, and exam readiness. |
| `study-politics` | Politics domain model that keeps textbook wording separate from Derived content. |
| `study-exam-oriented-english` | Exam-oriented English model for simple, accurate writing and natural English-to-Chinese translation. |
| `practice` | Generates separate printable questions and answers PDFs with provenance and a new practice run record. |
| `exam` | Closed-book assessment runner for a frozen Subject snapshot. It records first-pass answers, grading, error analysis, and learning gaps. |
| `exam hit` | Read-only question-by-question coverage test against a frozen graph snapshot. It derives HIT/PARTIAL/MISS/UNRESOLVED from actual card content. |
| `review` | Runs full-paper Exam Hit, content-level highlights, evidence-backed gap research, Material Review, and eligible Learner Review without mutating the frozen Exam Result. |
| `check` | Read-only QA and audit front door for source integrity, structure, questions, relations, retrieval, rendering, and readiness. |
| `sort` | Review-priority projection based on exam value, risk, dependencies, weakness, and recent errors. It does not change knowledge content. |
| `fix` | Repairs allowed Derived, Runtime, and Generated Artifact defects from a current `check` report. |
| `profile` | Records user-reported weaknesses, thinking habits, explanation preferences, and self-observations. It keeps self-reports separate from system observations. |
| `heal` | Runs a fresh cold-start novice loop or `heal exam` exam-driven knowledge-coverage iteration, with bounded routing and no Learner Model mutation. |
| `optimize` | Analyzes Derived cards and graph structure, then applies only authorized safe migrations with explicit provenance. |
| `amend` | Applies explicit user feedback to supplement or correct an existing learning artifact. It preserves Source and official provenance and runs local validation. |
| `help` | Read-only command reference for all workflows, subcommands, inputs, outputs, and data impacts. |

`learn` is the cross-subject front door. Use `study-math` when a task needs a
systematic mathematics graph, many questions, formulas, proofs, or exam-specific
mathematics structure.

`study-politics` is a domain model loaded by `learn`. It defines political
concepts, principles, canonical wording, comparisons, confusions, timelines,
policy frameworks, and question mappings.

`study-exam-oriented-english` is a domain model loaded by `learn`. It defines
reusable expression functions, writing-task structure, Chinese-idea-to-English
bridges, sentence-level writing review, long-sentence translation analysis,
meaning-preserving simplification, and evidence-backed language diagnostics.
It does not optimize for advanced vocabulary or ornate sentence complexity.

## Boundaries between skills

`check` does not build or repair content. It resets `.check/current/`, reads the
current artifact, runs isolated auditors, and reports evidence, root causes,
severity, and repair owners. Agent capacity changes parallelism, not audit
scope.

`fix` consumes one fresh `check` report and applies allowed repairs. It does not
modify Source, ask for per-finding confirmation, invoke `relearn`, or duplicate
the migration logic in `update`. Run `check` after `fix` to verify the result.

`heal` optimizes learning experience. It creates a fresh synthetic novice for
each round, records learning friction, and lets an independent Maintainer
accept, refine, reject, or block each finding. Synthetic traces never update
the real Learner Model. The run stops after pedagogical convergence, no
progress, a blocker, optimization oscillation, or at most five repair rounds.

`exam` reads the original exam and explanation PDFs directly. It does not use
OCR, OCR output, external OCR services, or delegated OCR. If a page cannot be
read reliably, the exam record marks it as unreadable.

`exam hit` reads the complete original exam against one frozen graph snapshot.
It checks actual card content rather than titles, question mappings, answer
history, or preselected priorities. It is not a learner score and never writes
Learner State. `heal exam` consumes its PARTIAL, MISS, and UNRESOLVED records.

`practice` owns question and answer PDF generation. `review` consumes the
closed Exam Result by default, or explicitly reads a user's own submission PDF
in `user-written` mode. Learner Review writes only eligible human evidence to
the local Learner Model; Material Review can process agent runs, consume a
native-text material catalog, emit question/card study focuses plus
Markdown/HTML and annotation overlays, and never write mastery. Review never
generates a PDF.

Exam owns `PDF → Exam Hit → Independent Answer → Grade → Freeze`. Review
consumes the frozen Hit output, then runs `Highlight → Gap Detection → Research
→ learn handoff → Recheck → Report`. Original hits and coverage gained after a
validated supplement remain separate snapshots and overlay stages.

`optimize` is the graph-structure boundary used by `heal`: it detects exact
duplicates, oversized or fragmented cards, and related-but-distinct concepts,
then records a migration plan. Analyze is read-only; semantic merge/split/
deletion operations require explicit confirmation and complete migration
evidence.

## Architecture

`learn` owns shared platform workflows:

```text
Source and provenance
Knowledge graph
Question Bank foundations
Progress
Search
Canonical Markdown
HTML and Site output
Common learner state
```

`study-math` owns mathematics cognition:

```text
Mathematics cards
Mathematics hierarchy
Typed semantic relations
Question operations and solution actions
Formula and MathObject integrity
Answer evidence
Active recall
Mathematics exam readiness
```

All skills write to the same Subject canonical Markdown, knowledge graph, and
learner state. `math-records.json` is a structured intermediate record, not a
second mathematics database.

## Mathematics model

`study-math` supports these seven card types:

```text
definition
theorem
formula
method
problem-pattern
comparison
bridge
```

Every card has one `recallPrompt` and one atomic
`atomicity.coreQuestion`. A chapter overview is module metadata, not a large
review card.

Questions remain separate from cards. Every question has exactly one
`primaryCardId`. Other cards use `secondaryCardIds`. Question text, solutions,
answers, and sources keep independent status fields. Lost formulas, truncated
solutions, and historical answers never become complete content silently.

## Repository layout

```text
plugin/
├─ plugin.json
├─ schemas/
│  └─ learner/
└─ skills/
   ├─ learn/
   ├─ update/
   ├─ relearn/
   ├─ study-math/
   ├─ study-politics/
   ├─ study-exam-oriented-english/
   ├─ practice/
   ├─ exam/
   ├─ review/
   ├─ help/
   ├─ check/
   ├─ sort/
   ├─ fix/
   ├─ profile/
   ├─ amend/
   ├─ heal/
   └─ optimize/
tests/
```

## Local validation

Run these commands from the repository root:

```powershell
python -X utf8 plugin/skills/study-math/scripts/validate_math.py plugin/skills/study-math/examples/math-records.json

python -X utf8 plugin/skills/study-math/scripts/validate_math_cards.py plugin/skills/study-math/examples/math-records.json --require-type definition --require-type theorem --require-type formula --require-type method --require-type problem-pattern --require-type comparison --require-type bridge

python -X utf8 plugin/skills/study-math/scripts/validate_markup.py plugin/skills/study-math

python -X utf8 -m unittest discover -s tests -v
```

`validate_math.py` checks structured records and mathematics readiness gates.
`validate_math_cards.py` checks card atomicity, card size, and type fields.
`validate_markup.py` checks Markdown math delimiters and raw LaTeX commands.
Inspect generated HTML separately for formulas, search, card interaction, and
browser console errors.

Each playbook loads only the schemas, integrity rules, rendering rules, and
agent roles needed for the current task. The front door stays stable while
individual workflows evolve.

## Evidence rules

Learning content keeps these evidence classes separate:

```text
Original material
External supplement
Derived question answer
Readable part of an official explanation
Needs verification
```

External pages may clarify a definition, condition, proof, or background. They
must not silently repair the original question or turn a Derived answer into an
official answer. When Source is incomplete, keep the Question Record and set an
explicit `questionStatus`, `solutionStatus`, or `answerStatus`.

## Contributing

Contributions are welcome under the GNU Affero General Public License v3.0 or later. Keep Source and Derived data
separate, preserve provenance, add or update deterministic validators for new
contracts, and run the relevant test suite before opening a pull request.

## Copyright

Copyright (c) 2026 YAN ZHIZHONG.
