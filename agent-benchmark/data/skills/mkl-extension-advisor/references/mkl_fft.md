# mkl_fft reference

Load this when the scanned code uses `np.fft.*`, `scipy.fft.*`, or `scipy.fftpack.*`.

## What it accelerates

A Python interface over Intel oneMKL DFTI. Covered transforms:

- Complex-to-complex: `fft`, `ifft`, `fft2`, `ifft2`, `fftn`, `ifftn`
- Real-to-complex: `rfft`, `rfft2`, `rfftn`
- Complex-to-real: `irfft`, `irfft2`, `irfftn`
- Hermitian: `hfft`, `ihfft` (via the numpy_fft interface)

Handles strided / non-contiguous arrays without a forced copy. Preserves single precision: `float32 -> complex64`, `float64 -> complex128` (stock NumPy upcasts to double).

## What it does NOT accelerate (honest NO)

- FFT helpers: `fftfreq`, `rfftfreq`, `fftshift`, `ifftshift`. mkl_fft ships its own copies built from basic NumPy array ops (`np.arange`, `np.roll`); they are not MKL-accelerated.
- Tiny / one-off transforms where dispatch overhead dominates.
- Extended precision: `np.longdouble`/`float128`/`clongdouble`/`complex256` are not computed in extended precision (downcast or not implemented, platform-dependent).
- Non-FFT work.

## Decide fit

Helps most on: large transforms, batched or N-D transforms along axes, repeated FFTs in a loop, real-input transforms (`rfft*`), multi-core machines. Candidate dtypes: float32/float64/complex64/complex128.

## Capability probe (no version strings)

```python
import mkl_fft
has_patch = hasattr(mkl_fft, "patch_numpy_fft")          # explicit-patch workflow available
has_scipy = hasattr(mkl_fft.interfaces, "scipy_fft")      # scipy backend available (needs scipy)
```

## Activation (minimal change)

NumPy FFT, process-wide:
```python
import mkl_fft
mkl_fft.patch_numpy_fft()
# ... np.fft.* now routes to mkl_fft ...
mkl_fft.restore_numpy_fft()
```
NumPy FFT, scoped:
```python
import mkl_fft
with mkl_fft.mkl_fft():
    result = np.fft.fft2(a)
```
SciPy FFT (backend, not a numpy patch):
```python
import scipy.fft
import mkl_fft.interfaces.scipy_fft as mkl_scipy_fft
with scipy.fft.set_backend(mkl_scipy_fft):
    result = scipy.fft.fft(x)
```
The `scipy_fft` interface covers the SciPy FFT surface, including hermitian 2-D/N-D transforms not in the numpy interface (`hfft2`, `ihfft2`, `hfftn`, `ihfftn`), and exposes `get_workers`/`set_workers` (worker control lives only on `scipy_fft`, not `numpy_fft`).

Patching is idempotent; it must run before the target call; it is thread-unsafe to patch while other threads run transforms. If numpy is already build-wired (see proof), do NOT add a redundant patch; offer always-patch only as an explicit portability option.

## Proof it is active

- `np.fft.fft.__module__ == "mkl_fft.interfaces._numpy_fft"` means FFT is active (build-wired or patched).
- Do NOT use `mkl_fft.is_patched()` to judge FFT: on build-wired numpy, FFT is active while `is_patched()` still returns False. `is_patched()` only tracks the explicit patch counter.

## Caveats

- `mkl_fft.*` direct functions use first arg `x`; `interfaces.numpy_fft.*` use `a`. Same call patterns otherwise.
- `irfft*` may copy the input because it writes into it; do not rely on the input being untouched.
- `scipy_fft` defaults workers to the max MKL threads (not SciPy's default of 1); results identical, thread usage differs.
