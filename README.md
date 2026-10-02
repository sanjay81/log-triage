# Log Triage

## What it does:

This proof of concept sends an automated test failure log to an OpenAI model and asks it for a structured category, root cause, evidence, and confidence. A deterministic `validate` step checks the response fields, `check_evidence` flags evidence that cannot be found in the log, and a final human-review guardrail marks uncertain, unsupported, or uninformative results for review instead of treating the model label as authoritative. An uninformative-log code rule catches logs that contain only generic “Test failed” and retry lines.

## Findings:

- The model can turn a failure log into a structured triage result.
- Deterministic validation rejects malformed categories, root causes, evidence fields, and confidence values.
- Evidence checking flags quotes that do not appear in the source log.
- Low confidence, missing evidence, unsupported evidence, or an `unknown` category can trigger human review.
- Uninformative logs get flagged by a code rule, not by trusting the label.

## Limitations:

There are only 3 sample logs, results come from single runs, and the substring check is strict: evidence must match text in the log after whitespace and case normalization. The uninformative-log rule is intentionally simple and may need adjustment for other log formats.

## Next:

Build a labeled set of 40 logs, measure classification accuracy against those labels, and add the deterministic checks and review flag to CI.

## Run

Set `OPENAI_API_KEY`, then run:

```sh
python triage.py sample_logs/hil_flash_timeout.log
```

Optionally set `OPENAI_MODEL` to choose a model. Dependencies are listed in `requirements.txt`.
