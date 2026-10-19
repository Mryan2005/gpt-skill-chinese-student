# Analyze optimization

1. Load the current Derived card, relation, question-mapping, and projection
   records. Capture their fingerprint and keep Source, Exam Result, and Learner
   State read-only.
2. Detect exact duplicates from normalized content and explicit provenance.
   Use supplied fragment groups and split signals for fragmented or oversized
   cards; do not infer a merge from a similar title alone.
3. Emit one stable operation ID per recommendation with evidence, risk,
   target IDs, expected migration, and a no-op reason where appropriate.
4. Validate the report and save it to the current optimize workspace. Do not
   apply recommendations in analyze mode.
