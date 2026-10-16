"""Validate Markdown math delimiters and reject bare LaTeX commands."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


LATEX_COMMAND = re.compile(
    r"(?<!\\)\\(?:frac|dfrac|tfrac|sqrt|sum|prod|int|lim|limsup|liminf|mathrm|mathbf|mathbb|text|left|right|"
    r"alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|phi|omega|infty|times|cdot|pm|leq|geq|neq|approx|"
    r"partial|nabla|underline|overline|begin|end|quad|qquad|cdots|ldots)\b|(?<!\\)\\%"
)

MATH_SPANS = [
    re.compile(r"\$\$(?:.|\n)*?\$\$"),
    re.compile(r"\\\[(?:.|\n)*?\\\]"),
    re.compile(r"\\\((?:.|\n)*?\\\)"),
    re.compile(r"(?<!\\)\$(?!\$)(?:\\.|[^$\n])+(?<!\\)\$(?!\$)"),
]


def iter_markdown(paths: list[Path]):
    seen: set[Path] = set()
    for raw_path in paths:
        path = raw_path.resolve()
        candidates = [path] if path.is_file() else sorted(path.rglob("*.md"))
        for candidate in candidates:
            candidate = candidate.resolve()
            if candidate not in seen and candidate.is_file():
                seen.add(candidate)
                yield candidate


def mask_code(source: str) -> str:
    source = re.sub(
        r"(?ms)^\s*```.*?^\s*```\s*$",
        lambda match: "\n" * match.group(0).count("\n"),
        source,
    )
    return re.sub(r"`[^`\n]*`", lambda match: " " * len(match.group(0)), source)


def mask_math(source: str) -> str:
    masked = source
    for pattern in MATH_SPANS:
        masked = pattern.sub(
            lambda match: "".join("\n" if char == "\n" else " " for char in match.group(0)),
            masked,
        )
    return masked


def check_file(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    code_free = mask_code(source)
    errors: list[str] = []
    for opening, closing in (("$$", "$$"), (r"\[", r"\]"), (r"\(", r"\)")):
        if code_free.count(opening) != code_free.count(closing):
            errors.append(f"{path}: unmatched math delimiter {opening}/{closing}")
    single_dollars = re.sub(r"\$\$", "", code_free).count("$")
    if single_dollars % 2:
        errors.append(f"{path}: unmatched inline math delimiter $")
    unmasked = mask_math(code_free)
    for match in LATEX_COMMAND.finditer(unmasked):
        line = unmasked.count("\n", 0, match.start()) + 1
        column = match.start() - unmasked.rfind("\n", 0, match.start())
        errors.append(f"{path}:{line}:{column}: LaTeX command outside math delimiters: {match.group(0)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Markdown math delimiters and LaTeX placement.")
    parser.add_argument("paths", nargs="+", type=Path, help="Markdown files or directories to scan")
    args = parser.parse_args(argv)
    files = list(iter_markdown(args.paths))
    if not files:
        print("No Markdown files found.", file=sys.stderr)
        return 2
    errors = [error for path in files for error in check_file(path)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: checked {len(files)} Markdown file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
