# MKL extension advisor: Seeded regression test

Read the end-user request in `request.md`. Analyze it as an advisor; do not install packages, benchmark code, or modify the request.

Write two deliverables:

- `advice.json`: the machine-checkable decision record described below.
- `advice.md`: the user-facing recommendation with conditional changes, short reasons, caveats, and proof steps.

Use case id `NO-3` and these scope ids exactly: `test_pricer_regression`.

`advice.json` must use this shape:

The values in this example illustrate the schema only. Derive every value from the request. When a scope has no suggestions, use `confirmation.required: false` with an empty package list and `install_guidance` mode `none`.

```json
{
  "schema_version": "mkl-extension-advice.v1",
  "case_id": "NO-3",
  "environment": {"assumed": false, "strategy": "probe", "checks": ["fft_module"]},
  "scope": [{"id": "function_name", "verdict": "suggestions", "packages": ["mkl_fft"]}],
  "findings": [
    {"call": "np.fft.fft", "surface": "fft", "package": "mkl_fft", "verdict": "fit", "reason_codes": ["covered_transform"]}
  ],
  "package_verdicts": {"mkl_fft": "fit", "mkl_random": "not_present", "mkl_umath": "not_present"},
  "confirmation": {"required": false, "packages": []},
  "changes_applied": false,
  "install_guidance": {"mode": "conditional", "pip_index_mode": "primary", "conda_override_channels": true},
  "proofs": ["fft_module"],
  "summary": "Concise verdict"
}
```

Use one `findings` entry for every relevant candidate call in the request. Use a distinct call spelling from the request for each entry. Allowed environment strategies are `probe`, `ask`, `conditional`, and `not_applicable`. Scope verdicts are `suggestions`, `no_suggestions`, and `out_of_scope`. Package verdicts are `fit`, `no_fit`, `not_present`, and `out_of_scope`. Finding verdicts are `fit`, `no_fit`, and `out_of_scope`; use package `none` for a finding outside all three extensions.

Reason codes should be concise identifiers such as `covered_transform`, `repeated_transform`, `bulk_sampling`, `legacy_random_api`, `reproducibility_change`, `covered_ufunc`, `covered_square`, `large_array`, `scalar_negligible`, `modern_generator_unsupported`, `unsupported_ufunc`, `unsupported_power`, `exact_sequence_required`, `blas_lapack_out_of_scope`, `already_wired_possible`, `non_numpy`, `gpu_out_of_scope`, or `integer_op_unsupported`.

Do not claim measured speedups. Do not claim the user's code appeared in documentation. Do not apply a change before user confirmation.
