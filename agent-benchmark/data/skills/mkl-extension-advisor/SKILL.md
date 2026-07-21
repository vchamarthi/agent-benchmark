---
name: mkl-extension-advisor
description: Use when a user wants to speed up NumPy or SciPy code on Intel CPUs and asks whether the Intel MKL extension packages (mkl_fft, mkl_random, mkl_umath) apply, or points at a snippet, function, file, or codebase that uses np.fft, np.random, or element-wise math ufuncs. DO NOT use for GPU work, non-Intel CPUs, mkl-service thread tuning, general profiling, or performance analysis beyond these three packages.
---

# mkl-extension-advisor

Given a piece of NumPy or SciPy code, decide whether the Intel MKL extension packages help it, and present verified change suggestions with short reasons. This is a fit check, not a profiler. Scope is exactly three packages: `mkl_fft`, `mkl_random`, `mkl_umath`.

You do not need every package's detail up front. Scan first, then load only the reference for each extension the code actually implicates.

## How MKL acceleration works (two axes)

- Install-time: which numpy binary is present and what it links against.
- Runtime: whether call sites dispatch to oneMKL, set by activation or by build-level pre-wiring.

Intel's pip numpy is build-wired (FFT and umath already dispatch to MKL with no activation call). Stock numpy (conda-forge or PyPI) leaves the extensions dormant until you patch. Determine which you have at runtime, do not assume from a version.

## Procedure

1. Take the input: a snippet, function, file, or codebase.
2. Scan every call site and categorize each into a candidate surface:
   - FFT: `np.fft.*`, `scipy.fft.*`, `scipy.fftpack.*` -> candidate for mkl_fft
   - Random: `np.random.*`, `np.random.RandomState`, `np.random.default_rng`/`Generator` -> candidate for mkl_random
   - Element-wise math ufuncs on arrays (trig, hyperbolic, exp/log, sqrt/cbrt, arithmetic) -> candidate for mkl_umath
3. For each DISTINCT candidate surface found, load only that extension's reference before judging it:
   - mkl_fft -> read `references/mkl_fft.md`
   - mkl_random -> read `references/mkl_random.md`
   - mkl_umath -> read `references/mkl_umath.md`
   Do not load a reference for a surface the code does not use.
4. Establish the install axis once (shared by all surfaces). CAUTION: an empty or non-mkl threadpool result BEFORE any BLAS call is not proof numpy lacks MKL; `threadpool_info()` only reports the MKL pool after a BLAS call loads it. Run a BLAS op first, then check:
   ```python
   import numpy as np
   from threadpoolctl import threadpool_info
   _ = np.random.rand(256, 256) @ np.random.rand(256, 256)  # force MKL BLAS to load
   mkl_backed = any(d.get("internal_api") == "mkl" for d in threadpool_info())
   ```
   Also read `np.fft.fft.__module__` to tell build-wired (`mkl_fft.interfaces._numpy_fft`) from stock (`numpy.fft`).
5. Judge each candidate call site against the loaded reference: does that extension actually cover this call and this usage? Decide fit, including honest NO. The reference lists what each package covers, what it does NOT cover, and its capability probe (`hasattr`, no version strings).
6. Mark each applicable site to a suggestions list: the file/location, the call, the minimal change, and the one-line reason it helps THIS code. Do not add a redundant patch on an already-wired surface.
7. Re-check coverage: confirm the entire input (every call site in the snippet, function, file, or codebase) has been scanned and judged before presenting. Do not stop after the first hit.
8. Present the result:
   - If there are suggestions: a structured list, grouped by file/location, each with the code change in a properly formatted diff or code block and a short reason. Include the install channels (below) if the packages are missing, the proof step for each surface (from its reference), and the mkl_random confirmation gate where relevant.
   - If there are no suggestions: say so honestly and explicitly. State that none of mkl_fft, mkl_random, or mkl_umath help this code and why (e.g. only uncovered ufuncs, only the modern Generator API, only tiny arrays, only FFT helpers, or no MKL-relevant calls at all). Do not invent a benefit.
9. Apply only on confirmation. Show the suggestions first; edit files after the user says yes. mkl_random requires an explicit OK every time (it changes results, see its reference).

## Guard rails

- Do not cite performance or speedup numbers. You have not measured this user's workload. State direction ("benefit grows with array size") without a figure unless the user gives you a measured source.
- Do not claim to have found the user's code in any document or README. Reason only from the code the user gave you.
- Decisions come from runtime feature detection (hasattr, bound-function `__module__`, threadpoolctl), never from a version string.
- Import the top-level package and call the function on it (`import mkl_fft; mkl_fft.patch_numpy_fft()`). Do not import from private submodules and do not invent function names; each reference lists the exact activation calls.
- Proof of "FFT active" is `np.fft.fft.__module__`, not `is_patched()`. See each reference for its reliable proof.

## Install channels

conda (Intel channel first, conda-forge second, override the rest):
```bash
conda install -c https://software.repos.intel.com/python/conda \
  -c conda-forge --override-channels \
  "blas=*=*_intelmkl" mkl_fft mkl_random mkl_umath
```
pip (Intel index as the primary index):
```bash
pip install --index-url https://software.repos.intel.com/python/pypi \
  numpy scipy mkl_fft mkl_random mkl_umath
```
Use `--index-url`, not `--extra-index-url`: Intel's index is a partial mirror, and extra-index lets pip prefer PyPI's stock numpy wheel. `threadpoolctl` is not mirrored; install it from PyPI separately. Consequence: the pip path gives build-wired FFT/umath (zero activation); the conda path gives stock numpy that needs explicit patching but gives control over the numpy build and OpenMP runtime.

## References (load on demand)

- `references/mkl_fft.md` - FFT: covered transforms, SciPy backend, activation, proof, caveats.
- `references/mkl_random.md` - random sampling: covered API, reproducibility hazard, activation, proof.
- `references/mkl_umath.md` - element-wise ufuncs: full covered list, what is NOT covered, activation, proof.
