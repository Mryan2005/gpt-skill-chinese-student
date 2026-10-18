"""Extract structured question material from native PDF text layers.

This is a material-source intake step. It does not OCR, solve questions, or
mutate the frozen Exam Result. Pages whose native text cannot be parsed remain
absent from the catalog and are reported as source gaps.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


YEAR_RANGES = {
    2009: (1, 10), 2010: (11, 19), 2011: (20, 27), 2012: (28, 35),
    2013: (36, 44), 2014: (45, 53), 2015: (54, 62), 2016: (63, 71),
    2017: (72, 80), 2018: (81, 89), 2019: (90, 98), 2020: (99, 107),
    2021: (108, 117), 2022: (118, 127), 2023: (128, 138),
}
QUESTION_MARKER = re.compile(r"(?m)^\s*\*?\s*(\d{1,2})\s*[\.．、,:：]\s*")
# Options are frequently printed two or four per line. The whitespace
# boundary keeps inline B/C/D options while avoiding letters embedded in words.
OPTION_MARKER = re.compile(r"(?<!\S)([A-D])\s*[\.．、,:：]\s*")
SOLUTION_MARKER = re.compile(r"(?m)^\s*(\d{1,2})\s*[\.．、,:：]?\s*【答案】\s*([A-D]+)?")


def _run_pdftotext(pdf: Path, start_page: int | None = None, end_page: int | None = None) -> str:
    executable = shutil.which("pdftotext")
    if not executable:
        raise RuntimeError("pdftotext is required for native PDF material intake")
    command = [executable]
    if start_page is not None:
        command.extend(["-f", str(start_page)])
    if end_page is not None:
        command.extend(["-l", str(end_page)])
    command.extend(["-layout", str(pdf), "-"])
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext failed for {pdf}: {result.stderr[-500:]}")
    return result.stdout


def clean_text(value: str) -> str:
    value = value.replace("\r", "").replace("\f", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n[ \t]+", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _question_metadata(exam_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(question.get("questionId")): question for question in exam_result.get("questions", []) if isinstance(question, dict)}


def _split_options(raw: str) -> tuple[str, list[dict[str, str]]]:
    matches = list(OPTION_MARKER.finditer(raw))
    if len(matches) < 2:
        return clean_text(raw), []
    stem = clean_text(raw[:matches[0].start()])
    options: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        text = clean_text(raw[match.end():end])
        if text:
            options.append({"letter": match.group(1), "text": text})
    return stem, options


def parse_question_block(text: str, year: int, metadata: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    markers = list(QUESTION_MARKER.finditer(text))
    selected: list[re.Match[str]] = []
    cursor = 0
    for number in range(1, 39):
        match = next((candidate for candidate in markers if candidate.start() >= cursor and int(candidate.group(1)) == number), None)
        if match is None:
            break
        selected.append(match)
        cursor = match.end()
    result: list[dict[str, Any]] = []
    for index, match in enumerate(selected):
        number = int(match.group(1))
        end = selected[index + 1].start() if index + 1 < len(selected) else len(text)
        raw = text[match.end():end]
        question_id = f"politics-{year}-q{number:02d}"
        source = metadata.get(question_id, {})
        question_type = source.get("type")
        if question_type in {"single_choice", "multiple_choice"} or number <= 33:
            stem, options = _split_options(raw)
        else:
            stem, options = clean_text(raw), []
        if number <= 33:
            status = "COMPLETE" if stem and len(options) >= 4 else "INCOMPLETE_TEXT_LAYER"
        else:
            status = "COMPLETE" if len(stem) >= 40 else "INCOMPLETE_TEXT_LAYER"
        page = source.get("examPage", {}).get("page") if isinstance(source.get("examPage"), dict) else None
        result.append({
            "id": question_id,
            "questionId": question_id,
            "year": year,
            "originalNumber": number,
            "type": question_type or ("single_choice" if number <= 16 else "multiple_choice" if number <= 33 else "analysis"),
            "stem": stem,
            "options": options,
            "questionStatus": status,
            "sourceRefs": [{"kind": "exam_question", "path": source.get("examPage", {}).get("path"), "page": page, "readingMode": source.get("examPage", {}).get("readingMode", "native_pdf_text")}] if source.get("examPage") else [],
            "officialAnswer": source.get("official", {}).get("answer") if isinstance(source.get("official"), dict) else None,
            "officialSolutionStatus": source.get("official", {}).get("solutionStatus") if isinstance(source.get("official"), dict) else "UNKNOWN",
        })
    return result


def parse_solution_text(text: str, year: int, source_path: Path) -> dict[int, dict[str, Any]]:
    markers = list(SOLUTION_MARKER.finditer(text))
    solutions: dict[int, dict[str, Any]] = {}
    for index, match in enumerate(markers):
        number = int(match.group(1))
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        raw = text[match.end():end]
        explanation = raw.split("【解析】", 1)[1] if "【解析】" in raw else raw
        explanation = clean_text(explanation)
        solutions[number] = {
            "sourcePath": str(source_path),
            "sourcePage": text[:match.start()].count("\f") + 1,
            "sourceAnswer": match.group(2) or None,
            "solutionText": explanation,
            "solutionStatus": "COMPLETE" if explanation else "ANSWER_ONLY",
        }
    return solutions


def _solution_paths(exam_result: dict[str, Any]) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for raw in exam_result.get("solutionPdfsRead", []):
        path = Path(raw)
        match = re.search(r"(20\d{2})", path.name)
        if match:
            result[int(match.group(1))] = path
    return result


def extract_material_catalog(exam_result: dict[str, Any], exam_pdf: Path, canonical_catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = _question_metadata(exam_result)
    questions: list[dict[str, Any]] = []
    for year, (start, end) in YEAR_RANGES.items():
        block = _run_pdftotext(exam_pdf, start, end)
        questions.extend(parse_question_block(block, year, metadata))
    solutions: dict[tuple[int, int], dict[str, Any]] = {}
    for year, path in _solution_paths(exam_result).items():
        if not path.exists():
            continue
        text = _run_pdftotext(path)
        for number, solution in parse_solution_text(text, year, path).items():
            solutions[(year, number)] = solution
    for question in questions:
        solution = solutions.get((question["year"], question["originalNumber"]))
        if solution:
            question.update(solution)
            question["solutionProvenance"] = "original_pdf_native_text"
        else:
            question["solutionText"] = ""
            question["solutionProvenance"] = "unavailable_or_non_text_pdf"
    base = canonical_catalog or {}
    base_questions = [question for question in base.get("questions", []) if isinstance(question, dict)]
    merged_questions = {str(question.get("id")): question for question in base_questions if question.get("id")}
    for question in questions:
        merged_questions[question["id"]] = question
    expected_ids = {str(question.get("questionId")) for question in exam_result.get("questions", []) if isinstance(question, dict) and question.get("questionId")}
    parsed_ids = {question["questionId"] for question in questions}
    return {
        "schemaVersion": "material-catalog.v2",
        "subjectId": base.get("subjectId") or exam_result.get("subject", {}).get("id"),
        "artifactVersion": base.get("artifactVersion") or exam_result.get("snapshot", {}).get("artifactVersion"),
        "sourcePolicy": "original_pdf_native_text_only",
        "cards": base.get("cards", base.get("nodes", [])),
        "questions": [merged_questions[key] for key in sorted(merged_questions)],
        "relations": base.get("relations", base.get("edges", [])),
        "materialSourceStats": {
            "expectedExamQuestionCount": len(expected_ids),
            "parsedQuestionCount": len(questions),
            "completeQuestionTextCount": sum(question.get("questionStatus") == "COMPLETE" for question in questions),
            "solutionTextCount": sum(bool(question.get("solutionText")) for question in questions),
            "sourceGaps": sorted((expected_ids - parsed_ids) | {question["questionId"] for question in questions if question.get("questionStatus") != "COMPLETE"}),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract native-text question material without OCR.")
    parser.add_argument("--exam-result", type=Path, required=True)
    parser.add_argument("--exam-pdf", type=Path, required=True)
    parser.add_argument("--canonical-catalog", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        exam_result = json.loads(args.exam_result.read_text(encoding="utf-8"))
        canonical = json.loads(args.canonical_catalog.read_text(encoding="utf-8")) if args.canonical_catalog else None
        catalog = extract_material_catalog(exam_result, args.exam_pdf, canonical)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "output": str(args.output), "stats": catalog["materialSourceStats"]}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
