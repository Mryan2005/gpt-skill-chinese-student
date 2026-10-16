# Question integrity

## Use this playbook when

Use it when questions are missing, duplicated, incomplete, mapped to the wrong card, or inconsistent with their solutions and answers.

## Procedure

1. Check Question IDs, source identity, original number, type, stem, options, figures, and subparts.
2. Check question, solution, answer, and source statuses independently.
3. Check duplicate fingerprints and question-group splitting.
4. Load the domain contract and verify primary mapping, secondary tags, tested operations, and answer evidence.
5. Emit findings with repairOwner learn/question-set or the domain model.

## Gate

The audit preserves every real incomplete question and identifies the earliest wrong boundary. It does not re-map or rewrite a Question.
