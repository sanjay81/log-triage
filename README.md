# AI-Assisted Log Triage

[![Log Triage CI](https://github.com/sanjay81/log-triage/actions/workflows/ci.yml/badge.svg)](https://github.com/sanjay81/log-triage/actions/workflows/ci.yml)


A small **AI-for-QA proof of concept** that combines an OpenAI model with deterministic validation rules to triage automated-test failure logs.

The goal is not to let an LLM become the authority. Instead, the model proposes a structured classification and supporting evidence, while ordinary code verifies the response and routes uncertain results to human review.

## What it demonstrates

- Structured failure classification from test logs.
- Suggested root cause, evidence, and confidence.
- Deterministic schema/value validation.
- Evidence verification against the original source log.
- Human-review guardrails for low-confidence or unsupported results.
- A rule-based path for uninformative logs.
- A roadmap toward measurable accuracy using a labeled dataset.

## Processing flow

```text
Failure log
    |
    v
OpenAI model
    |
    v
Structured triage result
    |
    +--> validate fields/category/confidence
    |
    +--> verify evidence exists in source log
    |
    +--> apply deterministic log-quality rules
    |
    v
Accept result or flag for human review
```

## Why the guardrails matter

LLM output is treated as a **proposal**, not ground truth. The POC checks:

- malformed categories or fields
- invalid confidence values
- missing evidence
- evidence not present in the original log
- `unknown` classifications
- generic logs containing little diagnostic information

Any of these conditions can trigger human review.

## Current findings

- The model can turn synthetic failure logs into structured triage output.
- Deterministic validation can reject malformed responses.
- Evidence checking catches unsupported quotations.
- Human review can be triggered instead of accepting uncertain output.
- Simple code rules are useful for cases where the input log itself is not informative enough.

## Limitations

The current dataset contains only three sample logs, and results are based on single runs. Evidence matching is intentionally strict: after whitespace/case normalization, supporting evidence must exist in the source log. The uninformative-log rule is also deliberately simple and will need adaptation for other log formats.

## Run

Set your API key in the environment:

```bash
export OPENAI_API_KEY="your-key"
python triage.py sample_logs/hil_flash_timeout.log
```

Optionally set `OPENAI_MODEL` to select a model. Dependencies are listed in `requirements.txt`.

## Next milestone

Build a labeled set of approximately 40 failure logs and measure:

- classification accuracy
- unsupported-evidence rate
- human-review rate
- deterministic validation failures
- repeatability across runs

The next engineering step is to integrate those checks into CI so AI-assisted triage has a measurable quality gate.

---

**Primary technologies:** Python · OpenAI API · LLM evaluation · Test Automation · Log Analysis · AI-assisted QA
