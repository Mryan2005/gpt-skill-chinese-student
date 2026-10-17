# Analyze errors

## Use this playbook when

Use it after grading to explain why answers failed and produce Learning Gap Reports and Repair Requests.

## Procedure

1. Read the immutable first pass, grading evidence, retrieval result, used cards, and official solution boundary.
2. Assign evidence-backed generic error types from error-taxonomy.md.
3. Load the domain model for domain-specific subtypes. For mathematics, read study-math math-exam guidance when available.
4. Separate learner performance errors from graph/artifact defects.
5. Produce one Repair Request per proposed repair. Include owner, evidence, reason, and suggested operation.
6. Keep the Exam Result immutable, then append evidence-backed observations to
   the local Learner Model after grading. Update derived Error Model, Mastery,
   and Explanation Model aggregates only through their local contracts.

## Gate

Every repair request points to learn or a domain model. exam never applies its
own content repair, and it never writes learner hints into the frozen snapshot.
