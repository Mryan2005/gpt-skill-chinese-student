# Change impact

Every plugin release that changes content or domain contracts can declare:

~~~json
{
  "version": "0.3.0",
  "migrations": ["source-derived-separation", "typed-relations-v2"],
  "affectedDomains": ["generic", "math", "politics"],
  "requiresArtifactRebuild": true,
  "requiresSourceReread": false
}
~~~

update uses this declaration to avoid rewriting unaffected Subjects. The report names affected domains, skipped domains, artifact rebuilds, source rereads, and blockers.
