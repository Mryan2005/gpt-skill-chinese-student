# Generate practice PDFs

Use this playbook when the user asks for a practice paper, printable test,
answer sheet, or a new set of questions for later review.

1. Load reliable question records and reject incomplete records unless their
   `questionStatus` explicitly preserves the uncertainty.
2. Reset only the exact `.practice/current/` target by moving an existing run
   into `.practice/history/<runId>/`.
3. Render `questions.pdf` without answers, solutions, hidden answer metadata,
   or answer-bearing page scripts.
4. Render `answers.pdf` with the same stable question IDs and detailed answer
   evidence. Label official, historical, derived, and unresolved answers.
   When the selected domain is `study-exam-oriented-english`, render writing
   requirements and answer space, or the original translation sentence; keep
   reference expressions, logic relations, and alternative translations in the
   answer record with provenance.
5. Write `practice-manifest.json` with question provenance, card links, PDF
   hashes, and generation policy. Write `practice-record.json` with no user
   attempt until a later submission exists.
6. Run `validate_practice.py`, render representative pages with Poppler, and
   inspect the rendered pages. A successful file write is not enough.

The practice generator may create answer files in the controlled local
workspace, but must record that answer access is withheld until submission if
the local filesystem cannot enforce access isolation.
