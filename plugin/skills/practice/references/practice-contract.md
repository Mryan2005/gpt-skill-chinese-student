# Practice contract

## Input record

The generator consumes `practice-input.v1`:

- `subjectId`, `title`, and optional `scope`, `durationMinutes`, and `totalPoints`;
- a non-empty ordered `questions` list;
- each question's stable `questionId`, `type`, `stem`, points, provenance, and
  optional options, figures, card IDs, and answer records.
- For the exam-oriented English domain, a writing question may add
  `writingRequirements`, `wordCount`, and `answerSpaceLines`; a translation
  question may add `sourceText`, `keyTerms`, and `logicRelations`. Its answer
  record may add a reference essay, paragraph analysis, simple reusable
  phrases, recommended translation, and common mistranslations. These remain
  Derived teaching fields and retain their own provenance.

An answer record uses independent fields such as `officialAnswer`,
`historicalAnswer`, `derivedAnswer`, `officialSolution`, `derivedSolution`,
`answerStatus`, and `solutionStatus`. It must not merge a derived answer into
an official answer field.

## PDF boundary

`questions.pdf` is the learner-facing input. `answers.pdf` is released only
after submission in a controlled workflow. Neither PDF is a replacement for
the structured provenance records.

Review never creates a PDF. It reads `questions.pdf`, `answers.pdf`, and an
optional `user-submission.pdf` directly with the model's native PDF/page
reading capability. OCR and OCR-generated transcripts are prohibited.

## History and attempts

Every generation gets a `practiceRunId`. Existing current artifacts move to
history before replacement. Each user submission gets a new immutable
`attemptId`; repeated work on the same paper is not an overwrite.
