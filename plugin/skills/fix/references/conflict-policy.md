# Fix conflict policy

1. Deterministic validators and deterministic repairs run first.
2. Fixers may analyze the same snapshot in parallel.
3. Proposals that touch the same file, entity, JSON path, or generated artifact
   are merged by the orchestrator, never written concurrently.
4. A proposal with incompatible values, low confidence, or missing evidence is
   marked `NEEDS_REVIEW` and remains unresolved.
5. Later phases cannot apply until their declared dependencies pass local
   validation.
6. A proposal that edits Source, official material, or an original question is
   rejected and produces `BLOCKED_BY_SOURCE`.
7. Repeatedly applying the same proposal without reducing its finding
   fingerprint produces `FIX_NO_PROGRESS` and stops the run.

The user does not receive an approval prompt for ordinary allowed repairs. The
final Fix Report records every rejected, blocked, or escalated proposal.
