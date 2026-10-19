"""Generate separate practice question and answer PDFs from practice-input.v1."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _paragraph(text: Any, style: ParagraphStyle) -> Paragraph:
    value = escape(str(text or "")).replace("\n", "<br/>")
    return Paragraph(value, style)


def _register_fonts() -> None:
    if "STSong-Light" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("practice-title", parent=base["Title"], fontName="STSong-Light", fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=10),
        "subtitle": ParagraphStyle("practice-subtitle", parent=base["Normal"], fontName="STSong-Light", fontSize=10, leading=15, alignment=TA_CENTER, textColor=colors.HexColor("#4b5a56"), spaceAfter=10),
        "h1": ParagraphStyle("practice-h1", parent=base["Heading1"], fontName="STSong-Light", fontSize=15, leading=21, spaceBefore=12, spaceAfter=8),
        "h2": ParagraphStyle("practice-h2", parent=base["Heading2"], fontName="STSong-Light", fontSize=12, leading=18, spaceBefore=8, spaceAfter=5),
        "body": ParagraphStyle("practice-body", parent=base["BodyText"], fontName="STSong-Light", fontSize=10, leading=16, alignment=TA_LEFT, spaceAfter=5),
        "small": ParagraphStyle("practice-small", parent=base["BodyText"], fontName="STSong-Light", fontSize=8, leading=12, textColor=colors.HexColor("#57635f"), spaceAfter=3),
        "question": ParagraphStyle("practice-question", parent=base["BodyText"], fontName="STSong-Light", fontSize=11, leading=18, spaceAfter=7),
        "option": ParagraphStyle("practice-option", parent=base["BodyText"], fontName="STSong-Light", fontSize=10, leading=16, leftIndent=8, spaceAfter=3),
    }


def _footer(canvas: Any, document: Any) -> None:
    canvas.saveState()
    canvas.setFont("STSong-Light", 8)
    canvas.setFillColor(colors.HexColor("#68746f"))
    canvas.drawString(18 * mm, 10 * mm, "中式学生 · practice")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"第 {document.page} 页")
    canvas.restoreState()


def _header(input_data: dict[str, Any], styles: dict[str, ParagraphStyle], answer: bool) -> list[Any]:
    title = f"{input_data.get('title', 'Practice')}｜{'答案与解析' if answer else '练习试卷'}"
    story: list[Any] = [_paragraph(title, styles["title"])]
    if input_data.get("scope"):
        story.append(_paragraph(f"范围：{input_data['scope']}", styles["subtitle"]))
    if not answer:
        meta = [
            f"题量：{len(input_data.get('questions', []))}",
            f"总分：{input_data.get('totalPoints', '—')}",
            f"建议时间：{input_data.get('durationMinutes', '—')} 分钟",
        ]
        story.append(_paragraph("　".join(meta), styles["subtitle"]))
        story.append(_paragraph("注意事项：" + "；".join(input_data.get("instructions", [])), styles["body"]))
    else:
        story.append(_paragraph("答案文件应在提交后开放。答案来源、派生答案和不确定性均按记录单独标记。", styles["subtitle"]))
    story.append(Spacer(1, 5 * mm))
    return story


def _figure(path_value: Any) -> Image | None:
    if not path_value:
        return None
    path = Path(str(path_value))
    if not path.is_file():
        return None
    image = Image(str(path))
    image._restrictSize(155 * mm, 75 * mm)
    return image


def _question_story(question: dict[str, Any], styles: dict[str, ParagraphStyle], answer: bool) -> list[Any]:
    number = question.get("number", "?")
    q_type = question.get("type", "question")
    parts: list[Any] = [_paragraph(f"{number}. [{question.get('questionId', '')}] [{q_type}]", styles["h2"]), _paragraph(question.get("stem", ""), styles["question"])]
    if question.get("formula"):
        parts.append(_paragraph(f"公式：{question['formula']}", styles["question"]))
    if question.get("type") == "translation" and question.get("sourceText"):
        parts.append(_paragraph(f"英文原文：{question['sourceText']}", styles["question"]))
    if not answer and question.get("writingRequirements"):
        parts.append(_paragraph(f"写作要求：{question['writingRequirements']}", styles["body"]))
    if not answer and question.get("wordCount"):
        parts.append(_paragraph(f"建议字数：{question['wordCount']}", styles["small"]))
    figure = _figure(question.get("figurePath"))
    if figure:
        parts.extend([figure, Spacer(1, 3 * mm)])
    if not answer:
        for option in question.get("options", []):
            if isinstance(option, dict):
                parts.append(_paragraph(f"{option.get('letter', '')}. {option.get('text', '')}", styles["option"]))
        space_lines = int(question.get("answerSpaceLines", 3 if q_type in {"single_choice", "multiple_choice", "true_false"} else 8))
        space_lines = max(1, min(space_lines, 40))
        parts.append(_paragraph("作答：" + "_" * 72, styles["small"]))
        for _ in range(space_lines - 1):
            parts.append(_paragraph("_" * 88, styles["small"]))
    else:
        official = question.get("officialAnswer")
        historical = question.get("historicalAnswer")
        derived = question.get("derivedAnswer")
        if official:
            parts.append(_paragraph(f"标准答案（官方）：{official}", styles["body"]))
        elif historical:
            parts.append(_paragraph(f"历史答案（未独立核实）：{historical}", styles["body"]))
        elif derived:
            parts.append(_paragraph(f"AI 独立推导答案（非官方）：{derived}", styles["body"]))
        else:
            parts.append(_paragraph("答案状态：待核实；当前不提供确定答案。", styles["body"]))
        for label, value in (
            ("答案状态", question.get("answerStatus")),
            ("解题过程", question.get("officialSolution") or question.get("derivedSolution")),
            ("核心考点", question.get("coreKnowledge")),
            ("关键步骤", question.get("keySteps")),
            ("易错点", question.get("pitfalls")),
            ("评分依据", question.get("rubric")),
            ("参考作文", question.get("referenceEssay")),
            ("段落结构", question.get("paragraphAnalysis")),
            ("可复用简单句式", question.get("simplePhrases")),
            ("可替换表达", question.get("alternativeExpressions")),
            ("常见语法错误", question.get("commonGrammarErrors")),
            ("推荐译文", question.get("recommendedTranslation")),
            ("关键词", question.get("keyTerms")),
            ("逻辑关系", question.get("logicRelations")),
            ("常见误译", question.get("commonMistranslations")),
            ("其他合理译法", question.get("alternativeTranslations")),
            ("来源与 provenance", question.get("sourceRefs")),
            ("不确定性", question.get("uncertainty")),
        ):
            if value:
                parts.append(_paragraph(f"{label}：{value}", styles["body"]))
    return [KeepTogether(parts)]


def _build_pdf(path: Path, input_data: dict[str, Any], answer: bool) -> None:
    _register_fonts()
    styles = _styles()
    document = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=17 * mm, title=input_data.get("title", "Practice"))
    story = _header(input_data, styles, answer)
    for index, question in enumerate(input_data.get("questions", [])):
        story.extend(_question_story(question, styles, answer))
        if index < len(input_data.get("questions", [])) - 1:
            story.append(Spacer(1, 5 * mm))
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)


def _archive_current(output_dir: Path, run_id: str) -> None:
    if not output_dir.exists() or not any(output_dir.iterdir()):
        return
    history = output_dir.parent / "history"
    history.mkdir(parents=True, exist_ok=True)
    archive = history / f"{run_id}-previous"
    counter = 1
    while archive.exists():
        archive = history / f"{run_id}-previous-{counter}"
        counter += 1
    shutil.move(str(output_dir), str(archive))
    output_dir.mkdir(parents=True, exist_ok=True)


def generate(input_data: dict[str, Any], output_dir: Path, run_id: str) -> dict[str, Any]:
    if input_data.get("schemaVersion") != "practice-input.v1":
        raise ValueError("schemaVersion must be practice-input.v1")
    questions = input_data.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("questions must be a non-empty list")
    ids = [question.get("questionId") for question in questions]
    if any(not isinstance(value, str) or not value.strip() for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("questionId values must be unique and non-empty")
    _archive_current(output_dir, run_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    questions_pdf = output_dir / "questions.pdf"
    answers_pdf = output_dir / "answers.pdf"
    _build_pdf(questions_pdf, input_data, answer=False)
    _build_pdf(answers_pdf, input_data, answer=True)
    manifest = {
        "schemaVersion": "practice-manifest.v1",
        "practiceRunId": run_id,
        "subjectId": input_data.get("subjectId"),
        "title": input_data.get("title"),
        "questionPdf": {"path": str(questions_pdf), "sha256": _sha256(questions_pdf)},
        "answerPdf": {"path": str(answers_pdf), "sha256": _sha256(answers_pdf), "releasePolicy": "withhold_until_submission"},
        "questions": [{
            "questionId": question.get("questionId"),
            "number": index + 1,
            "type": question.get("type"),
            "points": question.get("points"),
            "knowledgeCardIds": question.get("knowledgeCardIds", []),
            "sourceRefs": question.get("sourceRefs", []),
        } for index, question in enumerate(questions)],
        "generatedAt": _now(),
    }
    record = {
        "schemaVersion": "practice-record.v1",
        "practiceRunId": run_id,
        "state": "READY_FOR_ATTEMPT",
        "subjectId": input_data.get("subjectId"),
        "questionsPdf": manifest["questionPdf"],
        "answersPdf": manifest["answerPdf"],
        "answerReleased": False,
        "answerAccessLimitation": "Local filesystem output exists; do not expose answers before submission.",
        "attempts": [],
        "createdAt": manifest["generatedAt"],
    }
    (output_dir / "practice-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "practice-record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate separate practice question and answer PDFs.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    try:
        input_data = json.loads(args.input.read_text(encoding="utf-8"))
        run_id = args.run_id or f"practice-{uuid.uuid4().hex[:12]}"
        manifest = generate(input_data, args.output_dir, run_id)
        print(json.dumps({"status": "PASS", "practiceRunId": run_id, "outputDir": str(args.output_dir), "questionCount": len(manifest["questions"])}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, ImportError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
