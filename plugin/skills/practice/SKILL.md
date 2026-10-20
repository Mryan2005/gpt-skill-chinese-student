---
name: practice
description: Use to generate a printable or electronically answerable practice question PDF and a separate answer/explanation PDF. Do not use it to grade a submission or review an exam.
---

# Practice

`practice` generates a controlled practice run. It owns PDF authoring;
`review` reads the original PDFs and produces structured review output without
creating another PDF.

## Non-negotiables

- Generate separate `questions.pdf` and `answers.pdf` files.
- Keep stable question IDs, continuous numbering, points, type, provenance, and
  card links in `practice-manifest.json`.
- Never turn an incomplete source question into an official-looking question.
- Keep official, historical, and derived answers separate.
- Preserve prior `.practice/current/` runs in `.practice/history/` before a new
  run; never silently delete practice history.
- Do not expose answers during the question-generation phase. Filesystem
  isolation limits must be recorded in the practice record when applicable.
- Validate PDF integrity, page rendering, numbering, answer alignment, fonts,
  formulas, images, and missing content before reporting success.

Read [generate-pdf.md](playbooks/generate-pdf.md) and
[practice-contract.md](references/practice-contract.md) for the workflow.
Run [generate_practice_pdfs.py](scripts/generate_practice_pdfs.py) and
[validate_practice.py](scripts/validate_practice.py) for deterministic local
generation and validation.

## Outputs

```text
.practice/current/
├── questions.pdf
├── answers.pdf
├── practice-manifest.json
└── practice-record.json
```

`practice-record.json` records a run and attempts, but never invents a user
answer. A later `review user-written` run must use a new `attemptId`.
