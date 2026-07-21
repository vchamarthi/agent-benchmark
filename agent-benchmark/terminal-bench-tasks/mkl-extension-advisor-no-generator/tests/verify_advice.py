#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ADVICE_JSON = Path("/app/advice.json")
ADVICE_MD = Path("/app/advice.md")
EXPECTED = Path(sys.argv[1])


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def keyed(items, key, label):
    require(isinstance(items, list), f"{label} must be a list")
    result = {}
    for item in items:
        require(isinstance(item, dict) and item.get(key), f"each {label} entry needs {key}")
        require(item[key] not in result, f"duplicate {label} {key}: {item[key]}")
        result[item[key]] = item
    return result


def main():
    require(ADVICE_JSON.is_file(), "write /app/advice.json")
    require(ADVICE_MD.is_file(), "write /app/advice.md")
    actual = json.loads(ADVICE_JSON.read_text(encoding="utf-8"))
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    markdown = ADVICE_MD.read_text(encoding="utf-8", errors="replace")
    combined = json.dumps(actual, sort_keys=True) + "\n" + markdown
    lowered = combined.lower()

    require(actual.get("schema_version") == "mkl-extension-advice.v1", "wrong schema_version")
    require(actual.get("case_id") == expected["case_id"], "wrong case_id")
    require(actual.get("changes_applied") is False, "advisor must not apply changes before confirmation")
    require(len(markdown.strip()) >= 200, "advice.md is too short")

    actual_scope = keyed(actual.get("scope"), "id", "scope")
    require(set(actual_scope) == set(expected["scope"]), "scope must cover every expected unit exactly")
    for scope_id, rule in expected["scope"].items():
        row = actual_scope[scope_id]
        require(row.get("verdict") == rule["verdict"], f"wrong scope verdict for {scope_id}")
        require(set(row.get("packages", [])) == set(rule["packages"]), f"wrong scope packages for {scope_id}")

    actual_findings = keyed(actual.get("findings"), "call", "findings")
    finding_calls = "\n".join(actual_findings).lower()
    require("standard_normal" in finding_calls, "findings must address standard_normal")
    require("integers" in finding_calls, "findings must address integers")
    for call, row in actual_findings.items():
        require(row.get("package") == "mkl_random", f"wrong package for {call}")
        require(row.get("verdict") == "no_fit", f"wrong verdict for {call}")
        reasons = set(row.get("reason_codes", []))
        require("modern_generator_unsupported" in reasons, f"missing Generator reason for {call}")

    require(actual.get("package_verdicts") == expected["package_verdicts"], "wrong package verdicts")

    environment = actual.get("environment", {})
    require(environment.get("assumed") is False, "must not assume the user's environment")
    require(environment.get("strategy") in expected["environment"]["allowed_strategies"], "wrong environment strategy")
    checks = set(environment.get("checks", []))
    require(set(expected["environment"]["required_checks"]) <= checks, "missing environment checks")
    require(not checks.intersection(expected["environment"].get("forbidden_checks", [])), "forbidden environment check")

    confirmation = actual.get("confirmation", {})
    require(confirmation.get("required") is expected["confirmation"]["required"], "wrong confirmation requirement")
    require(set(confirmation.get("packages", [])) == set(expected["confirmation"]["packages"]), "wrong confirmation packages")

    install_guidance = actual.get("install_guidance", {})
    require(install_guidance.get("mode") == "none", "no-fit advice must not include installation guidance")
    require(set(expected.get("required_proofs", [])) <= set(actual.get("proofs", [])), "missing proof methods")

    for alternatives in expected.get("required_text_any", []):
        require(any(term.lower() in lowered for term in alternatives), f"missing one of: {alternatives}")
    for term in expected.get("forbidden_text", []):
        require(term.lower() not in lowered, f"forbidden claim or API: {term}")

    require(not re.search(r"\b\d+(?:\.\d+)?\s*(?:x|×)\b", lowered), "unverified speedup multiplier")
    require(not re.search(r"\b\d+(?:\.\d+)?\s*%\s+faster\b", lowered), "unverified speedup percentage")


if __name__ == "__main__":
    main()
