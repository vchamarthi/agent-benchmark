# mkl_random reference

Load this when the scanned code uses `np.random.*`, `np.random.RandomState`, or `np.random.default_rng`/`Generator`.

## What it accelerates

A Python interface over oneMKL's Vector Statistics Library (VSL) for bulk sampling. Covers the legacy `numpy.random` distribution API: `standard_normal`, `normal`, `rand`, `randn`, `uniform`, `poisson`, `exponential`, `gamma`, `binomial`, `beta`, `chisquare`, `choice`, and the rest of the named distributions, plus `seed`, `shuffle`, `permutation`.

`brng` generator families: MT19937 (default), SFMT19937, MT2203 (family, `('MT2203', id)`), R250, WH (family), MCG31, MCG59, MRG32K3A, PHILOX4X32X10, NONDETERM, ARS5. `skipahead`/`leapfrog` and the MT2203/WH families give independent parallel streams. `method` for normal: ICDF (default), BoxMuller, BoxMuller2.

## What it does NOT apply to (honest NO)

- The modern `np.random.default_rng()` / `Generator` API. mkl_random patches ONLY the legacy `np.random.*` functional API and `np.random.RandomState`. Generator-based code gets no benefit from patching. The only route is to construct `mkl_random.MKLRandomState(...)` explicitly, and only if the user accepts the reproducibility change.
- Tiny / scalar draws where vectorization has nothing to work on.
- Code that needs bit-for-bit reproducibility against numpy's stream (see hazard).

## Reproducibility hazard (mandatory caveat)

Patching mkl_random changes the sampling sequence for the same seed (confirmed: seed 0 differs from stock numpy, even with `brng='MT19937'`). The `method` choice also changes the stream. It is NOT a fixed-seed drop-in. Never apply it to code that depends on reproducible values without an explicit OK from the user, every time. Standard float methods return float64 (not 32-bit).

## Decide fit

Helps on: bulk legacy-API sampling with large `size`, Monte Carlo loops drawing many samples, parallel multi-stream Monte Carlo. Reproducibility-dependent code is a NO unless the user explicitly accepts changed values.

## Capability probe (no version strings)

```python
import mkl_random
has_patch = hasattr(mkl_random, "patch_numpy_random")
has_state = hasattr(mkl_random, "MKLRandomState")   # current class; the separate mkl_random.RandomState is deprecated (since 1.3.2)
```

## Activation (minimal change)

Patch the legacy API, process-wide:
```python
import mkl_random
mkl_random.patch_numpy_random()
# ... np.random.* now routes to VSL ...
mkl_random.restore_numpy_random()
```
Scoped:
```python
import mkl_random
with mkl_random.mkl_random():
    arr = np.random.standard_normal(1_000_000)
```
Explicit object. Prefer `MKLRandomState` (signature `MKLRandomState(seed=None, brng='MT19937')`). The separate `mkl_random.RandomState` class is deprecated since 1.3.2 and slated for removal; `mkl_random.interfaces.numpy_random.RandomState` is a distinct compatibility wrapper hardcoded to `brng='MT19937'`.
```python
import mkl_random
rng = mkl_random.MKLRandomState(seed=0, brng='MT19937')
x = rng.standard_normal(100_000_000, method='BoxMuller')
```
Patch/restore are reference-counted: N calls to `patch_numpy_random()` need N matching `restore_numpy_random()` calls to fully unpatch.

## Proof it is active

Unlike FFT, both are reliable here and flip together:
- `mkl_random.is_patched()` returns True after patching.
- `np.random.rand.__module__ == "mkl_random.interfaces._numpy_random"` when patched.
