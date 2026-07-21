from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

from agent_benchmarks.harnesses import load_task
from agent_benchmarks.skills import load_skill


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "data" / "skills" / "mkl-extension-advisor"
TASKS_ROOT = ROOT / "terminal-bench-tasks"
TASK_NAMES = {
    "mkl-extension-advisor-fit-dsp",
    "mkl-extension-advisor-no-generator",
    "mkl-extension-advisor-no-seeded-regression",
    "mkl-extension-advisor-env-detect",
}


def _extract_heredoc(script: str, target: str, marker: str) -> str:
    match = re.search(
        rf"cat > {re.escape(target)} <<'{marker}'\n(.*?)\n{marker}",
        script,
        re.DOTALL,
    )
    assert match, f"missing {target} heredoc"
    return match.group(1)


def _load_verifier(task_dir: Path):
    verifier_path = task_dir / "tests" / "verify_advice.py"
    spec = importlib.util.spec_from_file_location(
        f"verify_{task_dir.name.replace('-', '_')}", verifier_path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_skill_package_excludes_answer_key():
    skill = load_skill(SKILL_DIR)

    assert skill.name == "mkl-extension-advisor"
    assert {path.name for path in (SKILL_DIR / "references").glob("*.md")} == {
        "mkl_fft.md",
        "mkl_random.md",
        "mkl_umath.md",
    }
    assert not (SKILL_DIR / "examples").exists()
    assert not list(SKILL_DIR.rglob("*expected*"))


def test_pilot_advisor_tasks_have_complete_hidden_contracts():
    case_ids = set()
    for task_name in TASK_NAMES:
        task_dir = TASKS_ROOT / task_name
        task = load_task(task_dir)
        expected_path = task_dir / "tests" / "expected.json"
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

        assert "mkl_extension_advisor" in task.metadata["tags"]
        assert (task_dir / "environment" / "request.md").is_file()
        assert (task_dir / "solution" / "solve.sh").is_file()
        assert (task_dir / "tests" / "test.sh").is_file()
        assert (task_dir / "tests" / "verify_advice.py").is_file()
        assert expected["case_id"] not in case_ids
        case_ids.add(expected["case_id"])

    assert case_ids == {"FIT-1", "NO-1", "NO-3", "ENV-1"}


@pytest.mark.parametrize("task_name", sorted(TASK_NAMES))
def test_oracle_satisfies_hidden_verifier(task_name: str, tmp_path: Path):
    task_dir = TASKS_ROOT / task_name
    solve = (task_dir / "solution" / "solve.sh").read_text(encoding="utf-8")
    advice_json = tmp_path / "advice.json"
    advice_md = tmp_path / "advice.md"
    advice_json.write_text(
        _extract_heredoc(solve, "/app/advice.json", "JSON"), encoding="utf-8"
    )
    advice_md.write_text(
        _extract_heredoc(solve, "/app/advice.md", "MD"), encoding="utf-8"
    )

    verifier = _load_verifier(task_dir)
    verifier.ADVICE_JSON = advice_json
    verifier.ADVICE_MD = advice_md
    verifier.EXPECTED = task_dir / "tests" / "expected.json"
    verifier.main()


def test_verifier_rejects_noop(tmp_path: Path):
    task_dir = TASKS_ROOT / "mkl-extension-advisor-fit-dsp"
    verifier = _load_verifier(task_dir)
    verifier.ADVICE_JSON = tmp_path / "missing-advice.json"
    verifier.ADVICE_MD = tmp_path / "missing-advice.md"
    verifier.EXPECTED = task_dir / "tests" / "expected.json"

    with pytest.raises(AssertionError, match="write /app/advice.json"):
        verifier.main()


def test_no_generator_verifier_accepts_grouped_generator_coverage(tmp_path: Path):
    task_dir = TASKS_ROOT / "mkl-extension-advisor-no-generator"
    verifier = _load_verifier(task_dir)
    advice_json = tmp_path / "advice.json"
    advice_md = tmp_path / "advice.md"
    advice_json.write_text(
        json.dumps(
            {
                "schema_version": "mkl-extension-advice.v1",
                "case_id": "NO-1",
                "environment": {"assumed": False, "strategy": "not_applicable", "checks": []},
                "scope": [{"id": "draw_samples", "verdict": "no_suggestions", "packages": []}],
                "findings": [
                    {
                        "call": "rng.standard_normal(n)",
                        "surface": "random",
                        "package": "mkl_random",
                        "verdict": "no_fit",
                        "reason_codes": ["modern_generator_unsupported"],
                    },
                    {
                        "call": "rng.integers(0, 100, size=n)",
                        "surface": "random",
                        "package": "mkl_random",
                        "verdict": "no_fit",
                        "reason_codes": ["modern_generator_unsupported"],
                    },
                ],
                "package_verdicts": {
                    "mkl_fft": "not_present",
                    "mkl_random": "no_fit",
                    "mkl_umath": "not_present",
                },
                "confirmation": {"required": False, "packages": []},
                "changes_applied": False,
                "install_guidance": {"mode": "none"},
                "proofs": [],
                "summary": (
                    "The modern Generator API does not support the mkl_random patch. "
                    "An explicit MKLRandomState rewrite changes reproducibility."
                ),
            }
        ),
        encoding="utf-8",
    )
    advice_md.write_text(
        (
            "The modern Generator API is not accelerated by mkl_random. "
            "An explicit MKLRandomState rewrite changes reproducibility. "
        ) * 10,
        encoding="utf-8",
    )

    verifier.ADVICE_JSON = advice_json
    verifier.ADVICE_MD = advice_md
    verifier.EXPECTED = task_dir / "tests" / "expected.json"
    verifier.main()


def test_no_seeded_regression_verifier_accepts_argument_bearing_calls(tmp_path: Path):
    task_dir = TASKS_ROOT / "mkl-extension-advisor-no-seeded-regression"
    verifier = _load_verifier(task_dir)
    advice_json = tmp_path / "advice.json"
    advice_md = tmp_path / "advice.md"
    advice_json.write_text(
        json.dumps(
            {
                "schema_version": "mkl-extension-advice.v1",
                "case_id": "NO-3",
                "environment": {"assumed": False, "strategy": "not_applicable", "checks": []},
                "scope": [
                    {"id": "test_pricer_regression", "verdict": "no_suggestions", "packages": []}
                ],
                "findings": [
                    {
                        "call": "np.random.seed(0)",
                        "surface": "random",
                        "package": "mkl_random",
                        "verdict": "no_fit",
                        "reason_codes": ["exact_sequence_required"],
                    },
                    {
                        "call": "np.random.standard_normal(1_000_000)",
                        "surface": "random",
                        "package": "mkl_random",
                        "verdict": "no_fit",
                        "reason_codes": ["reproducibility_change"],
                    },
                ],
                "package_verdicts": {
                    "mkl_fft": "not_present",
                    "mkl_random": "no_fit",
                    "mkl_umath": "not_present",
                },
                "confirmation": {"required": False, "packages": []},
                "changes_applied": False,
                "install_guidance": {"mode": "none"},
                "proofs": [],
                "summary": "The seeded sequence must remain stable for the golden regression.",
            }
        ),
        encoding="utf-8",
    )
    advice_md.write_text(
        "The same seed produces a different sequence, so preserve the golden regression. " * 10,
        encoding="utf-8",
    )

    verifier.ADVICE_JSON = advice_json
    verifier.ADVICE_MD = advice_md
    verifier.EXPECTED = task_dir / "tests" / "expected.json"
    verifier.main()


def test_no_seeded_regression_verifier_allows_context_and_hard_no(tmp_path: Path):
    task_dir = TASKS_ROOT / "mkl-extension-advisor-no-seeded-regression"
    solve = (task_dir / "solution" / "solve.sh").read_text(encoding="utf-8")
    advice = json.loads(_extract_heredoc(solve, "/app/advice.json", "JSON"))
    advice["findings"].append(
        {
            "call": "run_pricer(shocks)",
            "surface": "user_function",
            "package": "none",
            "verdict": "out_of_scope",
            "reason_codes": ["non_numpy"],
        }
    )
    advice_json = tmp_path / "advice.json"
    advice_md = tmp_path / "advice.md"
    advice_json.write_text(json.dumps(advice), encoding="utf-8")
    advice_md.write_text(
        "Hard no: the same seed produces a different sequence and breaks golden 100.4237. " * 10,
        encoding="utf-8",
    )

    verifier = _load_verifier(task_dir)
    verifier.ADVICE_JSON = advice_json
    verifier.ADVICE_MD = advice_md
    verifier.EXPECTED = task_dir / "tests" / "expected.json"
    verifier.main()


def test_env_detect_verifier_accepts_fft_backend_module_alias(tmp_path: Path):
    task_dir = TASKS_ROOT / "mkl-extension-advisor-env-detect"
    solve = (task_dir / "solution" / "solve.sh").read_text(encoding="utf-8")
    advice = json.loads(_extract_heredoc(solve, "/app/advice.json", "JSON"))
    advice["environment"]["checks"] = ["fft_backend_module"]
    advice["proofs"] = ["fft_backend_module"]
    advice["confirmation"] = {"required": True, "packages": ["mkl_fft"]}
    advice_json = tmp_path / "advice.json"
    advice_md = tmp_path / "advice.md"
    advice_json.write_text(json.dumps(advice), encoding="utf-8")
    advice_md.write_text(
        _extract_heredoc(solve, "/app/advice.md", "MD"), encoding="utf-8"
    )

    verifier = _load_verifier(task_dir)
    verifier.ADVICE_JSON = advice_json
    verifier.ADVICE_MD = advice_md
    verifier.EXPECTED = task_dir / "tests" / "expected.json"
    verifier.main()