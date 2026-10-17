# Finding schema

The final merged report uses `check.finding.v1`. Individual auditors use the
same finding object inside an isolated `check.agent-report.v1` envelope.

Each finding has the following shape:

~~~json
{
  "id": "finding-001",
  "reportedBy": "source-auditor",
  "code": "META_AS_QUESTION",
  "severity": "blocker",
  "subject": "数学一",
  "entityType": "question",
  "entityId": "series-overview",
  "observed": "chapter_metadata was used as a Question source",
  "expected": "entityType=chapter_metadata must stay out of Question Bank",
  "evidence": [
    {
      "path": "records/sources.json",
      "locator": "sources[series-overview]",
      "detail": "entityType=chapter_metadata"
    }
  ],
  "rootLayer": "source-classification",
  "repairOwner": "learn/source-classification",
  "status": "open"
}
~~~

Required fields are id, reportedBy, code, severity, subject, entityType,
entityId, observed, expected, evidence, rootLayer, and repairOwner. `reportedBy`
must identify the isolated auditor or `finding-merger` that owns the report
entry. Evidence must point to a real file, record, node, question, URL, or
rendered location. status is open unless the audit is comparing a previously
recorded finding.

## Agent report envelope

Each isolated report under `.check/current/subagent-reports/` contains. Every
finding's `reportedBy` must equal the envelope's `agentId`; the merger preserves
that attribution in the final report.

~~~json
{
  "schemaVersion": "check.agent-report.v1",
  "agentId": "source-auditor",
  "runId": "math-1-check-001",
  "artifactVersion": "math-records.example.v1",
  "readOnly": true,
  "status": "completed",
  "checkedPaths": ["records/sources.json"],
  "executedChecks": ["source-manifest"],
  "skippedChecks": [],
  "findings": []
}
~~~

`status=skipped` or `status=failed` must include a reason in
`skippedChecks`. The merger must not consume a report with another run ID or
artifact version.

## Final result

The merged report has one `result`:

- `PASS`: no blocker, error, or warning remains;
- `PASS_WITH_WARNINGS`: warnings remain, but no blocker or error remains;
- `FAIL`: at least one blocker or error was found;
- `BLOCKED`: the workspace was not clean or a required auditor did not run.

An unexecuted required audit is never reported as a pass.

## Common codes

Use existing domain validator codes when available, including META_AS_QUESTION,
QUESTION_DUPLICATED, QUESTION_CARD_MISMATCH, MATH_CONTENT_LOSS,
RELATION_MISSING_TYPE, EMPTY_BRIDGE, and rendering or retrieval failures. The
cross-domain audit vocabulary also includes SOURCE_MISSING, SOURCE_MUTATED,
DERIVED_WITHOUT_PROVENANCE, AI_TEXT_MARKED_AS_SOURCE, SOURCE_ENTITY_UNMAPPED,
KNOWLEDGE_COVERAGE_GAP, CARD_TOO_BROAD, CARD_TOO_LARGE, CHAPTER_AS_CARD,
INVALID_CARD_TYPE, QUESTION_INCOMPLETE, SOLUTION_PROVENANCE_CONFLICT,
ANSWER_PROVENANCE_CONFLICT, FORMULA_SYNTAX_ERROR, RELATION_WRONG_DIRECTION,
PROVENANCE_AMBIGUOUS, RENDERING_FAILURE, RETRIEVAL_ZERO_HIT,
RETRIEVAL_AMBIGUOUS, and RETRIEVAL_WRONG_TARGET. The extended QA vocabulary
also includes CARD_NOT_ATOMIC, GROUP_USED_AS_REVIEW_CARD, DUPLICATE_ENTITY_ID,
QUESTION_COMPLETE_WITHOUT_SOLUTION, ANSWER_WITHOUT_REASONING,
DERIVED_MARKED_AS_OFFICIAL, SOLUTION_ANSWER_MISMATCH, INVALID_MATH_RELATION,
RELATION_REASON_TOO_GENERIC, RELATION_HEURISTIC_UNREVIEWED,
SOURCE_MUTATED_BY_DERIVATION, SOURCE_REFERENCE_BROKEN, LATEX_SYNTAX_ERROR,
FORMULA_SOURCE_MISMATCH, SOURCE_KNOWLEDGE_NOT_DERIVED, CONTENT_INCOMPLETE,
CONTENT_TOO_SHALLOW, and CONDITION_MISSING. Use a new code only when the
existing contract cannot express the finding.
