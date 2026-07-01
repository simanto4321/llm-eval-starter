# LLM Output Comparison

Compares two mock LLM responses on a coding puzzle using programmatic validation, rubric scoring, and automated Markdown reporting.

Uses **simulated model outputs** (no API key required).

## What it does

1. Presents a coding prompt (even-index sum puzzle)
2. Compares mock responses from `Model_A` and `Model_B`
3. Validates syntax, stdlib-only usage, O(n) heuristic, and correct logic
4. Scores accuracy, formatting, and helpfulness (1–5)
5. Writes `evaluation_report.md`

## Requirements

- Python **3.10+** (uses `sys.stdlib_module_names`)

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python llm_evaluator.py
```

Or on Windows:

```bat
run.bat
```

## Output

- Console summary with per-model validation and scores
- `evaluation_report.md` — formatted comparison report
