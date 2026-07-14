# LLM Output Comparison

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![CI](https://github.com/simanto4321/llm-eval-starter/actions/workflows/ci.yml/badge.svg)

Compares two mock LLM responses on a coding puzzle using programmatic validation, rubric scoring, and automated Markdown reporting.

No API key required — uses simulated model outputs.

## What it does

1. Presents a coding prompt (even-index sum puzzle)
2. Compares mock responses from `Model_A` and `Model_B`
3. Validates syntax, stdlib-only usage, O(n) heuristic, and correct logic
4. Scores accuracy, formatting, and helpfulness (1–5)
5. Writes `evaluation_report.md`

## Project structure

```
llm-eval-starter/
├── llm_evaluator.py
├── requirements.txt
├── run.bat
└── evaluation_report.md   # generated
```

## Requirements

- Python **3.10+** (uses `sys.stdlib_module_names`)

## Install

```bash
git clone https://github.com/simanto4321/llm-eval-starter.git
cd llm-eval-starter
pip install -r requirements.txt
```

No third-party packages required (stdlib only).

## Run

```bash
python llm_evaluator.py
```

Windows:

```bat
run.bat
```

## Results

| Model | Validation | Avg rubric |
|-------|--------------|------------|
| Model_A | PASS | 4.67 / 5 |
| Model_B | FAIL | 2.33 / 5 |

Winner: **Model_A**

## License

MIT — see [LICENSE](LICENSE).
