#!/usr/bin/env bash
set -euo pipefail

cat > /app/advice.json <<'JSON'
{
  "schema_version": "mkl-extension-advice.v1",
  "case_id": "NO-3",
  "environment": {
    "assumed": false,
    "strategy": "not_applicable",
    "checks": []
  },
  "scope": [
    {
      "id": "test_pricer_regression",
      "verdict": "no_suggestions",
      "packages": []
    }
  ],
  "findings": [
    {
      "call": "np.random.seed",
      "surface": "random",
      "package": "mkl_random",
      "verdict": "no_fit",
      "reason_codes": [
        "exact_sequence_required",
        "reproducibility_change"
      ]
    },
    {
      "call": "np.random.standard_normal",
      "surface": "random",
      "package": "mkl_random",
      "verdict": "no_fit",
      "reason_codes": [
        "exact_sequence_required",
        "reproducibility_change"
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
  "summary": "Do not change the random backend while the exact seeded golden result must remain unchanged."
}
JSON

cat > /app/advice.md <<'MD'
# Do not apply mkl_random

This regression depends on the exact values produced after `np.random.seed(0)`, as shown by the fixed `100.4237` golden assertion. mkl_random produces a different sequence for the same seed, so patching it is not a fixed-seed drop-in replacement and would invalidate the test.

I would refuse to apply the random change under the stated requirement. The user would first need to explicitly accept changed values and approve a newly validated golden result.

No FFT or umath surface appears here. The correct outcome is a guarded no-change recommendation, not installation or activation instructions.
MD
