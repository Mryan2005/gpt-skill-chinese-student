# Native PDF reading contract

## PDF SOURCE INTEGRITY GATE

During exam, the AI must read the original exam PDF directly.

1. Read the original exam PDF with the model or platform's native PDF/page-reading capability.
2. For scanned pages, inspect the rendered page image directly.
3. For text PDFs, native text may assist reading, but the original page remains authoritative when layout, formulas, figures, tables, or notation matter.
4. Read mathematical expressions, matrices, figures, tables, subscripts, fractions, and bounds from the original page.
5. Reference the original PDF and page in every question and official-solution evidence record.
6. If the page cannot be read reliably, record QUESTION_UNREADABLE or MATH_EXPRESSION_UNREADABLE. Do not reconstruct it silently.

## Prohibited substitutes

Do not use pytesseract, tesseract, easyocr, paddleocr, ocrmypdf, keras-ocr, doctr, any pip OCR package, an external OCR API, an OCR-generated text file, or a script that converts the page into a surrogate transcript before answering.

Do not use exam_ocr.txt, extracted_questions.json, temporary_transcript.md, solution_extracted.md, or an equivalent replacement as an answer source. The original exam PDF and original explanation PDF remain authoritative.

## Transitive prohibition

OCR prohibition applies transitively. No agent, subagent, script, subprocess, helper, or external service may OCR the exam or explanation PDF on behalf of exam. A delegated OCR result is still an OCR result and fails the gate.

## Allowed platform operations

Viewing a PDF page, zooming a page image, reading the PDF's native text layer, selecting a page, and inspecting a page region are allowed when they keep the original PDF as the source. These operations do not create a substitute input.
