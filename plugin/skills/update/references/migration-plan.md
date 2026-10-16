# Migration plan

A plan is an auditable list of small migrations. It is not a promise that every step can run automatically.

Each step records:

~~~text
id
kind: generic | domain
owner
fromVersion
toVersion
idempotent
sourceMutation: forbidden
requiresSourceReread
requiresArtifactRebuild
status
~~~

If requiresSourceReread is true, the plan must say why the old Derived record cannot preserve the source boundary. If the source is missing, stop with BLOCKED_BY_SOURCE.

The plan also records before/target metadata, an immutable snapshot reference, entity counts, hashes, affected domains, and finalGate=check.
