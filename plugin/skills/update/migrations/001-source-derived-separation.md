# 001: Source/Derived separation

Generic migration. Split mutable learning text from original Source records. Preserve source IDs, locators, hashes, and versions. Add provenance to Derived records. Never modify Source content.

If the old record does not contain enough information to identify original content, stop with BLOCKED_BY_SOURCE or NEEDS_REDERIVATION.
