"""
LLM Output Comparison.

Compares mock responses from two models on a coding logic puzzle,
runs programmatic validation, scores outputs, and writes a Markdown report.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Mock LLM responses (no API key required)
# ---------------------------------------------------------------------------

CODING_PROMPT = (
    "Fix the off-by-one error: given an array of integers, return the sum "
    "of elements at even indices (0, 2, 4, ...). Use only the Python "
    "standard library and O(n) time complexity."
)

MOCK_RESPONSES: dict[str, dict[str, str]] = {
    "Model_A": {
        "name": "Model_A",
        "response": '''```python
def sum_even_indices(arr):
    """Sum elements at even indices (0, 2, 4, ...)."""
    total = 0
    for i in range(0, len(arr), 2):
        total += arr[i]
    return total
```''',
    },
    "Model_B": {
        "name": "Model_B",
        "response": '''```python
import numpy as np

def sum_even_indices(arr):
  s = 0
  for i in range(1, len(arr), 2):
    s += arr[i]
  return s
```''',
    },
}


@dataclass
class ValidationResult:
    """Outcome of programmatic checks on a model response."""

    model_name: str
    passed: bool
    syntax_valid: bool
    stdlib_only: bool
    linear_time: bool
    fixes_off_by_one: bool
    details: list[str]


@dataclass
class HumanScore:
    """Rubric-style scores mimicking a human evaluator (1–5 scale)."""

    model_name: str
    accuracy: int
    formatting: int
    helpfulness: int
    notes: str

    @property
    def total(self) -> int:
        return self.accuracy + self.formatting + self.helpfulness

    @property
    def average(self) -> float:
        return round(self.total / 3, 2)


def extract_python_code(response: str) -> str:
    """Pull Python source from a fenced code block or raw text."""
    match = re.search(r"```(?:python)?\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return response.strip()


def check_syntax_valid(code: str) -> tuple[bool, str]:
    """Return whether code parses as valid Python."""
    try:
        ast.parse(code)
        return True, "Syntax is valid Python."
    except SyntaxError as exc:
        return False, f"Syntax error: {exc.msg} (line {exc.lineno})"


def check_stdlib_only(code: str) -> tuple[bool, str]:
    """Reject responses that import non-standard-library packages."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False, "Cannot check imports: invalid syntax."

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in sys.stdlib_module_names:
                    return False, f"Non-stdlib import detected: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root not in sys.stdlib_module_names:
                    return False, f"Non-stdlib import detected: {node.module}"
    return True, "Uses standard library only."


def check_linear_time(code: str) -> tuple[bool, str]:
    """
    Heuristic: single loop over input with step 2 suggests O(n).

    This is a simplified static check, not formal analysis.
    """
    has_range_len = "range" in code and "len(" in code
    no_nested_same_iter = code.count("for ") <= 1
    if has_range_len and no_nested_same_iter:
        return True, "Heuristic: single pass over array (likely O(n))."
    return False, "Heuristic: could not confirm linear-time single pass."


def check_fixes_off_by_one(code: str) -> tuple[bool, str]:
    """
    Check that the loop starts at index 0 with step 2 (even indices).

    Model_B intentionally starts at 1 — this check should fail for it.
    """
    pattern = re.search(
        r"range\s*\(\s*0\s*,\s*len\s*\([^)]+\)\s*,\s*2\s*\)",
        code.replace(" ", ""),
    )
    if pattern:
        return True, "Loop iterates even indices starting at 0."
    alt = re.search(r"range\s*\(\s*0\s*,\s*len", code)
    if alt and ", 2" in code:
        return True, "Loop appears to use start=0 with step 2."
    return False, "Does not clearly sum even indices (0, 2, 4, ...)."


def validate_response(model_name: str, response: str) -> ValidationResult:
    """Run all programmatic validators on one model response."""
    code = extract_python_code(response)
    details: list[str] = []

    syntax_ok, syntax_msg = check_syntax_valid(code)
    details.append(syntax_msg)

    stdlib_ok, stdlib_msg = check_stdlib_only(code) if syntax_ok else (False, "Skipped: invalid syntax.")
    details.append(stdlib_msg)

    linear_ok, linear_msg = check_linear_time(code) if syntax_ok else (False, "Skipped: invalid syntax.")
    details.append(linear_msg)

    fix_ok, fix_msg = check_fixes_off_by_one(code) if syntax_ok else (False, "Skipped: invalid syntax.")
    details.append(fix_msg)

    passed = syntax_ok and stdlib_ok and linear_ok and fix_ok
    return ValidationResult(
        model_name=model_name,
        passed=passed,
        syntax_valid=syntax_ok,
        stdlib_only=stdlib_ok,
        linear_time=linear_ok,
        fixes_off_by_one=fix_ok,
        details=details,
    )


def human_evaluate(validation: ValidationResult, response: str) -> HumanScore:
    """
    Score response like a human reviewer (1–5 per dimension).

    Uses validation outcomes plus simple formatting heuristics.
    """
    code = extract_python_code(response)
    has_docstring = '"""' in code or "'''" in code
    has_fence = "```" in response

    # Accuracy: heavily weighted by whether the puzzle was solved correctly.
    if validation.passed:
        accuracy = 5
    elif validation.syntax_valid and validation.fixes_off_by_one:
        accuracy = 4
    elif validation.syntax_valid:
        accuracy = 2
    else:
        accuracy = 1

    formatting = 4 if (has_fence and has_docstring) else (3 if has_fence else 2)

    helpfulness = 5 if validation.passed else (2 if validation.syntax_valid else 1)
    notes_parts = []
    if not validation.fixes_off_by_one:
        notes_parts.append("Incorrect index logic (off-by-one).")
    if not validation.stdlib_only:
        notes_parts.append("Used non-standard-library dependency.")
    if validation.passed:
        notes_parts.append("Correct, clean solution.")

    return HumanScore(
        model_name=validation.model_name,
        accuracy=accuracy,
        formatting=formatting,
        helpfulness=helpfulness,
        notes=" ".join(notes_parts) or "No additional notes.",
    )


def determine_winner(scores: list[HumanScore]) -> str:
    """Return winning model name or 'Tie'."""
    if len(scores) < 2:
        return scores[0].model_name if scores else "N/A"
    sorted_scores = sorted(scores, key=lambda s: (s.average, s.accuracy), reverse=True)
    if sorted_scores[0].average == sorted_scores[1].average:
        return "Tie"
    return sorted_scores[0].model_name


def build_markdown_report(
    prompt: str,
    validations: list[ValidationResult],
    scores: list[HumanScore],
    winner: str,
) -> str:
    """Build the evaluation report as a Markdown string."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# LLM Evaluation Report",
        "",
        f"**Generated:** {timestamp}  ",
        "",
        "## Prompt",
        "",
        f"> {prompt}",
        "",
        "## Programmatic Validation",
        "",
        "| Model | Syntax | Stdlib Only | O(n) Heuristic | Correct Logic | Overall |",
        "|-------|--------|-------------|----------------|---------------|---------|",
    ]

    for v in validations:
        lines.append(
            f"| {v.model_name} | {'✅' if v.syntax_valid else '❌'} | "
            f"{'✅' if v.stdlib_only else '❌'} | {'✅' if v.linear_time else '❌'} | "
            f"{'✅' if v.fixes_off_by_one else '❌'} | {'PASS' if v.passed else 'FAIL'} |"
        )

    lines.extend(["", "## Human-Style Rubric Scores (1–5)", ""])
    for s in scores:
        lines.extend([
            f"### {s.model_name}",
            "",
            f"- **Accuracy:** {s.accuracy}/5",
            f"- **Formatting:** {s.formatting}/5",
            f"- **Helpfulness:** {s.helpfulness}/5",
            f"- **Average:** {s.average}/5",
            f"- **Notes:** {s.notes}",
            "",
        ])

    lines.extend([
        "## Winner",
        "",
        f"**{winner}** — highest combined rubric score and validation pass rate.",
    ])
    return "\n".join(lines)


def write_report(content: str, output_path: Path) -> None:
    """Write Markdown report to disk."""
    output_path.write_text(content, encoding="utf-8")
    print(f"Report written to: {output_path}")


def main() -> None:
    """Run evaluation pipeline and emit Markdown report."""
    output_path = Path(__file__).resolve().parent / "evaluation_report.md"
    validations: list[ValidationResult] = []
    scores: list[HumanScore] = []

    print("=" * 60)
    print("LLM Output Comparison")
    print("=" * 60)

    for key in ("Model_A", "Model_B"):
        entry = MOCK_RESPONSES[key]
        name = entry["name"]
        response = entry["response"]
        print(f"\n--- Evaluating {name} ---")

        try:
            validation = validate_response(name, response)
            validations.append(validation)
            score = human_evaluate(validation, response)
            scores.append(score)

            print(f"  Validation: {'PASS' if validation.passed else 'FAIL'}")
            for detail in validation.details:
                print(f"    - {detail}")
            print(f"  Rubric average: {score.average}/5")
        except Exception as exc:
            print(f"  Error evaluating {name}: {exc}", file=sys.stderr)

    winner = determine_winner(scores)
    report = build_markdown_report(CODING_PROMPT, validations, scores, winner)
    write_report(report, output_path)

    print("\n" + "=" * 60)
    print(f"Winner: {winner}")
    print("=" * 60)


if __name__ == "__main__":
    main()
