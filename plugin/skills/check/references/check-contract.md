# Check contract

check reads Subject artifacts and produces findings. It does not own the learning content or any domain model.

## Inputs

- The current Subject and its version;
- canonical Markdown and knowledge-network HTML;
- Structured Records when the domain provides them;
- learner_state and task-state;
- the selected domain contract and validators.

## Read-only boundary

The audit may read files, parse records, run validators, open HTML, search, inspect console output, and write an isolated findings report. It must not modify the canonical Subject or use a repair as evidence for the original audit.

## Root-cause rule

Trace each observed failure toward the earliest wrong layer:

~~~text
rendering
↑
canonical output
↑
knowledge/question/relation records
↑
source classification and provenance
~~~

Report the first wrong boundary and the owner that should repair it. Do not hide a source error with a renderer filter.

## Domain boundary

The domain model defines what a valid card, question mapping, formula, relation, or readiness state means. check validates the artifact against that contract. It must not impose mathematical Card Types on a non-math Subject or impose a generic four-block card on a domain that declares another shape.

## Report contract

Write one structured finding per observed problem. The report includes a summary by severity, executed checks, skipped checks, findings, and the final audit status. Use validate_findings.py before handing the report back.
