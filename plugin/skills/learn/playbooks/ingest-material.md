# Ingest material

## Use this playbook when

Use it when the user supplies new images, PDFs, textbook pages, notes, or source files.

## Read

- [common.md](../references/common.md)
- [source-model.md](../references/source-model.md)
- [provenance.md](../references/provenance.md)
- [agent-contract.md](../references/agent-contract.md) for a complex batch

## Outcome

Create or extend Source Records without deciding a domain-specific card schema. Preserve order, locations, figures, formulas, unreadable regions, evidence labels, and question-group boundaries.

## Procedure

1. Read project state and inventory every supplied source in deterministic order.
2. Inspect each source in full. Record readable text, formulas, tables, figures, captions, and page breaks.
3. Classify each entity before mapping it to a Question or Knowledge Node.
4. Create stable Source IDs and an intake report in an isolated report directory.
5. Mark missing, conflicting, or unreadable content. Do not repair it from memory or an unrelated external source.
6. Hand the records to the goal-specific playbook and the selected domain model.

## Gate

Every input has a source entry, status, entityType, provenance, and unresolved-boundary record. No metadata, question group, or unclassified source enters Question Bank.
