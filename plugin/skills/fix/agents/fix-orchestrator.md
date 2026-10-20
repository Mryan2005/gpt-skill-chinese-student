# Fix Orchestrator

Validate the fresh check report, merge isolated Patch Proposals, and apply
allowed repairs serially in dependency order. It is the sole writer for Derived,
Runtime, and Generated Artifact changes and must stop on conflicts or protected
Source boundaries.
