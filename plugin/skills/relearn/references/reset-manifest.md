# Relearn reset manifest

The manifest is a one-time destructive action description:

~~~json
{
  "schemaVersion": "relearn-reset.v1",
  "action": "relearn",
  "state": "WAITING_FOR_USER_CONFIRMATION",
  "subject": {
    "id": "math-1",
    "root": "subject/math-1"
  },
  "deletePaths": [
    "derived",
    "canonical/math-1.md",
    "knowledge-network/index.html",
    "learner_state.md"
  ],
  "preservePaths": [
    "sources",
    "source-records.json",
    "originals",
    ".local/learner"
  ],
  "confirmation": {
    "required": true,
    "received": false
  }
}
~~~

The reset script refuses a manifest that deletes a preserve path or one of its parents. It also refuses to apply a manifest whose confirmation has not been recorded.
