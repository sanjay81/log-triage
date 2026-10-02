"""Task: send a failure log to an LLM and get structured JSON back.
 
Usage:
    export OPENAI_API_KEY="sk-..."          # Windows PowerShell: $env:OPENAI_API_KEY="sk-..."
    python triage.py sample_logs/hil_flash_timeout.log
 
Optional:
    export OPENAI_MODEL="gpt-4o-mini"       # any chat model you have access to
"""
import re
import json
import os
import sys

from openai import OpenAI

CATEGORIES = ["product_defect", "environment_issue", "test_issue", "flaky", "unknown"]


def is_uninformative_log(log_text: str) -> bool:
    """Detect logs with no diagnostic content using a simple deterministic rule."""
    meaningful_lines = [
        line.strip() for line in log_text.splitlines()
        if line.strip() and line.strip().lower() not in {"test failed"}
        and not re.fullmatch(r"retry\s+\d+\s*/\s*\d+", line.strip(), re.IGNORECASE)
    ]
    return not meaningful_lines

SYSTEM_PROMPT = f"""You are a senior embedded test engineer who triages failed
automated test runs (HIL, Embedded Linux, CAN, DLT, Robot Framework, CI pipelines).
 
Classify the failure into exactly one category:
- product_defect: the software under test behaves wrongly
- environment_issue: bench, hardware, network, flashing, power, or CI infrastructure problem
- test_issue: the test script, test data, or expectation is wrong
- flaky: intermittent, timing-dependent, not clearly any of the above
- unknown: the log does not contain enough information to decide
 
Respond ONLY with a JSON object with these keys:
- category: one of {CATEGORIES}
- root_cause: one short sentence
- evidence: list of 1-3 short quotes or facts taken from the log
- confidence: a number from 0.0 to 1.0
 
Rules: use only what is in the log. If the log is not enough, lower the confidence.
Do not invent log lines.

evidence items must be exact substrings copied from the log. Never describe the log. 
If there is no usable evidence, return an empty list.

"""

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def check_evidence(result: dict, log_text: str) -> dict:
    """Flag evidence items that do not appear in the log (possible hallucination)."""
    log_norm = _norm(log_text)
    result["unsupported_evidence"] = [
        e for e in result["evidence"] if _norm(e) not in log_norm
    ]
    return result


def call_llm(log_text: str) -> str:
    """The only function that knows about the provider. Swap this to change vendor."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) #reads OPENAI_API_KEY from the environment
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-nano"),
        temperature=1.0,  # lowest variation; still not guaranteed identical
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Failure log:\n\n{log_text}"},
        ],
    )
    usage = response.usage
    print(f"[tokens] prompt={usage.prompt_tokens} completion={usage.completion_tokens}",
          file=sys.stderr)
    return response.choices[0].message.content

def validate(result: dict) -> dict:
    """Deterministic checks. This is the part you will later turn into a CI gate."""
    if result.get("category") not in CATEGORIES:
        raise ValueError(f"Invalid category: {result.get('category')}")
    if not isinstance(result.get("root_cause"), str) or not result["root_cause"]:
        raise ValueError("Missing root_cause")
    if not isinstance(result.get("evidence"), list):
        raise ValueError("evidence must be a list")
    conf = result.get("confidence")
    if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
        raise ValueError(f"Invalid confidence: {conf}")
    return result

def apply_guardrails(result: dict) -> dict:
    """Downgrade answers that have no evidence or very low confidence."""
    result["needs_human_review"] = (
        result["category"] == "unknown"
        or not result["evidence"]
        or result["confidence"] < 0.5
        or bool(result["unsupported_evidence"])
        or result.get("uninformative_log", False)
    )
    return result

def triage(log_text: str) -> dict:
    raw = call_llm(log_text)
    result = check_evidence(validate(json.loads(raw)), log_text)
    result["uninformative_log"] = is_uninformative_log(log_text)
    return apply_guardrails(result)
 
if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python triage.py <logfile>")
    with open(sys.argv[1], encoding="utf-8") as f:
        log = f.read()
    print(json.dumps(triage(log), indent=2))
