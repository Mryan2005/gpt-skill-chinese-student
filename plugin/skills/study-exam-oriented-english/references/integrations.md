# Practice, review, optimize, and heal integration

## Practice

`practice` consumes English question records and writes its normal
`.practice/current/questions.pdf` and `answers.pdf`. Writing questions carry a
task type, requirements, word count, prompt material, and answer space.
Translation questions carry the original English text and answer space. The
answers PDF may contain a simple reference response, paragraph analysis,
meaning units, key terms, logic relations, common errors, and alternative
translations, each with provenance.

## Review

Use `chinese-student: review exam-result` for material analysis and
`chinese-student: review user-written` only when the learner explicitly submits
their own PDF. Review reads the original PDFs directly, preserves multiple
reasonable translations, and reports sentence-level evidence. It never creates
a PDF or turns an AI answer into learner evidence.

## Optimize

Use `chinese-student: optimize` to analyze repeated expression cards, repeated
translation techniques, oversized essay templates, over-split language cards,
missing grammar dependencies, and invalid classifications. Semantic
differences, register differences, and different logic must block a merge.

## Heal exam

`heal exam` can identify missing writing functions, grammar patterns, task
types, long-sentence structures, and logic-handling techniques from a supplied
exam PDF. It uses the shared maximum-five-round
`check → fix/learn → optimize → check` protocol. Web material is an explicitly
provenanced External Supplement and never a replacement for the original exam
or a universal high-score template.
