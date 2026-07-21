# End-user request

Speed this up on Intel, it's the hot loop in our audio pipeline.

```python
import numpy as np

def bandpass_batch(frames, lo_bin, hi_bin):
    # frames: float32 array, shape (n_frames, 8192)
    out = np.empty_like(frames)
    for i in range(frames.shape[0]):
        spec = np.fft.rfft(frames[i])
        spec[:lo_bin] = 0
        spec[hi_bin:] = 0
        out[i] = np.fft.irfft(spec, n=frames.shape[1])
    return out
```
