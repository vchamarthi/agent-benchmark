#!/usr/bin/env bash
set -euo pipefail

cat > /app/advice.json <<'JSON'
{
  "schema_version": "mkl-extension-advice.v1",
  "case_id": "FIT-1",
  "environment": {
    "assumed": false,
    "strategy": "probe",
    "checks": [
      "fft_module"
    ]
  },
  "scope": [
    {
      "id": "bandpass_batch",
      "verdict": "suggestions",
      "packages": [
        "mkl_fft"
      ]
    }
  ],
  "findings": [
    {
      "call": "np.fft.rfft",
      "surface": "fft",
      "package": "mkl_fft",
      "verdict": "fit",
      "reason_codes": [
        "covered_transform",
        "repeated_transform"
      ]
    },
    {
      "call": "np.fft.irfft",
      "surface": "fft",
      "package": "mkl_fft",
      "verdict": "fit",
      "reason_codes": [
        "covered_transform",
        "repeated_transform"
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
  "summary": "mkl_fft fits both repeated real FFT call sites, subject to runtime wiring detection."
}
JSON

cat > /app/advice.md <<'MD'
# Recommendation

`mkl_fft` fits both `np.fft.rfft` and `np.fft.irfft`: they are covered transforms repeated over 8192-point float32 frames, and the MKL interface preserves the float32-to-complex64 path.

Do not assume the environment. First inspect `np.fft.fft.__module__`. If it is `mkl_fft.interfaces._numpy_fft`, FFT dispatch is already active and no patch should be added. If it is stock `numpy.fft`, propose a scoped `with mkl_fft.mkl_fft():` block or `mkl_fft.patch_numpy_fft()` with a matching restore. Ask for confirmation before editing.

If the package is missing, use Intel's pip index as the primary `--index-url`, or use the Intel conda channel first with conda-forge and `--override-channels`. No random or umath extension is implicated by this hot loop.
MD
