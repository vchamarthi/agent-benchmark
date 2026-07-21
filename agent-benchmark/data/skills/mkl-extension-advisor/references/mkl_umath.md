# mkl_umath reference

Load this when the scanned code uses element-wise math ufuncs on arrays (`np.sin`, `np.exp`, `np.log`, etc.).

## What it accelerates

Swaps oneMKL VML kernels in as the C-level inner loops of NumPy's ufuncs, so existing `np.*` call sites are accelerated with no call-site rewrite. Covered ufuncs (from the installed source):

- Trig: `sin`, `cos`, `tan`, `arcsin`, `arccos`, `arctan`
- Hyperbolic: `sinh`, `cosh`, `tanh`, `arcsinh`, `arccosh`, `arctanh`
- Exp/log: `exp`, `exp2`, `expm1`, `log`, `log2`, `log10`, `log1p`
- Power/root: `sqrt`, `cbrt`, `square`, `reciprocal`
- Arithmetic: `add`, `subtract`, `multiply`, `divide`, `negative`, `positive`, `absolute`, `fabs`, `conjugate`, `sign`
- Rounding/float: `ceil`, `floor`, `trunc`, `rint`, `copysign`, `nextafter`, `spacing`, `frexp`, `ldexp`, `modf`
- Comparison: `equal`, `not_equal`, `greater`, `greater_equal`, `less`, `less_equal`
- Logical: `logical_and`, `logical_or`, `logical_xor`, `logical_not`
- Predicates: `isfinite`, `isinf`, `isnan`, `fmax`, `fmin`

## What it does NOT cover (honest NO)

- `maximum`, `minimum` (no dedicated MKL function).
- General `power` / `**` with an arbitrary exponent. Only `square`, `sqrt`, `cbrt`, `reciprocal` are covered (i.e. `**2`, `**0.5`, `**(1/3)`, `**-1`), NOT `a ** 2.5`.
- `arctan2`, `hypot`, `logaddexp`, `heaviside`, bitwise ops.
- Integer-only work (VML paths are float/double/complex).

## Size behavior

VML overhead means the win grows with array size; small arrays may not benefit and fall through to NumPy's native loops. Do NOT cite a specific element-count threshold: the cutoff lives in compiled code and is not verifiable from source, and it changes between versions.

## Decide fit

Helps most on: large float32/float64/complex arrays of transcendental math (`sin/cos/exp/log/sqrt` and the covered families) in hot, vectorized code. NO on: small arrays, uncovered functions (above), integer-only work, memory-bandwidth-bound cheap ops.

## Capability probe (no version strings)

```python
import mkl_umath
has_patch = hasattr(mkl_umath, "patch_numpy_umath")
```

## Activation (minimal change)

Process-wide:
```python
import mkl_umath
mkl_umath.patch_numpy_umath()
# ... np.sin/np.exp/... now use VML ...
mkl_umath.restore_numpy_umath()
```
Scoped:
```python
import mkl_umath
with mkl_umath.mkl_umath():
    y = np.sin(a) + np.exp(a)
```
(`restore` and `use_in_numpy` exist but are deprecated aliases; use the names above.) Patch before any threads run ufuncs; thread-unsafe to patch mid-computation.

## Proof it is active

- `mkl_umath.is_patched()` returns True when active. CAUTION: it can read True at import on build-wired numpy, or if `numpy` was imported before `mkl_umath`. Check it, but be explicit (call `patch_numpy_umath()` yourself) rather than relying on import side effects.
