# Review a user-written submission

Use only when the user explicitly says the submission is theirs or invokes
`chinese-student: review user-written`.

Inputs are `questions.pdf`, `answers.pdf`, and a new `user-submission.pdf`.
Read every original page directly with native PDF/page reading. Rendered page
images are allowed; OCR packages, OCR APIs, delegated OCR, and OCR transcripts
are prohibited.

Create a new immutable `attemptId`. Record question/page evidence for the
written answer, final answer after visible corrections, blank or unreadable
areas, and working steps. Do not confuse printed answers or annotations with
the user's answer.

Grade only against reliable answer/provenance records. Keep uncertain or
unreadable answers explicit. Update Learner State only for evidence-backed
human observations, idempotently. Generate diagnostics, highlights, learning
tasks, and retest plans as structured non-PDF outputs.

Do not modify the question PDF, answer PDF, Source, or canonical content. Do
not create a PDF review report.
