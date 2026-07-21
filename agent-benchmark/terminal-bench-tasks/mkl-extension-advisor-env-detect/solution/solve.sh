#!/usr/bin/env bash
set -euo pipefail

cat > /app/advice.json <<'JSON'
{
  "schema_version": "mkl-extension-advice.v1",
  "case_id": "ENV-1",
  "environment": {
    "assumed": false,
    "strategy": "probe",
    "checks": [
      "fft_module",
      "threadpool_after_blas"
    ]
  },
  "scope": [
    {
      "id": "fft_call",
      "verdict": "suggestions",
      "packages": [
        "mkl_fft"
      ]
    }
  ],
  "findings": [
    {
      "call": "np.fft.fft",
      "surface": "fft",
      "package": "mkl_fft",
      "verdict": "fit",
      "reason_codes": [
        "covered_transform",
        "already_wired_possible"
      ]
    }
  ],
  "package_verdicts": {
    "mkl_fft": "fit",
    "mkl_random": "not_present",
    "mkl_umath": "not_present"
  },
  "confirmation": {
    "required": false,
    "packages": []
  },
  "changes_applied": false,
  "install_guidance": {
    "mode": "conditional",
    "pip_index_mode": "primary",
    "conda_override_channels": true
  },
  "proofs": [
    "fft_module"
  ],
  "summary": "Probe the bound FFT function first; add a patch only for a stock NumPy FFT binding."
}
JSON

cat > /app/advice.md <<'MD'
# Check before changing anything

Run `np.fft.fft.__module__`. A value of `mkl_fft.interfaces._numpy_fft` proves that FFT dispatch is already active, whether it came from a build-wired NumPy or an explicit patch. In that state, add no redundant patch.

Do not use `mkl_fft.is_patched()` as the FFT proof: it can be false while build-wired FFT dispatch is active. After forcing a BLAS operation, threadpoolctl can separately identify the loaded NumPy BLAS backend, but that does not replace the bound FFT check.

Only if the function remains bound to stock `numpy.fft` should `patch_numpy_fft()` or a scoped mkl_fft context be proposed, subject to user confirmation.
MD
