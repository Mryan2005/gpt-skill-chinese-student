# Migrate

Create the planned snapshot, then execute one migration at a time. Before each step, verify its fromVersion. After each step, validate the new shape. Never mutate Source. Delegate semantic decisions to the domain model. Stop on NEEDS_REDERIVATION, BLOCKED_BY_SOURCE, or any failed invariant.
