#!/usr/bin/env bash
set -euo pipefail

cat > /app/advice.json <<'JSON'
{
  "schema_version": "mkl-extension-advice.v1",
  "case_id": "NO-1",
  "environment": {
    "assumed": false,
    "strategy": "not_applicable",
    "checks": []
  },
  "scope": [
    {
      "id": "draw_samples",
      "verdict": "no_suggestions",
      "packages": []
    }
  ],
  "findings": [
    {
      "call": "np.random.default_rng",
      "surface": "random",
      "package": "mkl_random",
      "verdict": "no_fit",
      "reason_codes": [
        "modern_generator_unsupported"
      ]
    },
    {
      "call": "rng.standard_normal",
      "surface": "random",
      "package": "mkl_random",
      "verdict": "no_fit",
      "reason_codes": [
        "modern_generator_unsupported"
      ]
    },
    {
      "call": "rng.integers",
      "surface": "random",
      "package": "mkl_random",
      "verdict": "no_fit",
      "reason_codes": [
        "modern_generator_unsupported"
      ]
    }
  ],
  "package_verdicts": {
    "mkl_fft": "not_present",
    "mkl_random": "no_fit",
    "mkl_umath": "not_present"
  },
  "confirmation": {
    "required": false,
    "packages": []
  },
  "changes_applied": false,
  "install_guidance": {
    "mode": "none",
    "pip_index_mode": "not_applicable",
    "conda_override_channels": false
  },
  "proofs": [],
  "summary": "mkl_random patching does not affect Generator-based code; an explicit state rewrite needs consent."
}
JSON

cat > /app/advice.md <<'MD'
# No recommendation as written

`mkl_random` does not patch `np.random.default_rng`, `Generator.standard_normal`, or `Generator.integers`. Applying the legacy NumPy random patch would have no effect on this function.

The only MKL-backed alternative is an explicit rewrite around `mkl_random.MKLRandomState`, and that is not a transparent replacement for Generator. It produces a different sequence and may also require API restructuring, which is a reproducibility change.

I would not modify this code unless the user explicitly accepts changed sequences and the explicit-object API. No FFT or umath surface is present, and no installation guidance is needed for the no-change verdict.
MD
