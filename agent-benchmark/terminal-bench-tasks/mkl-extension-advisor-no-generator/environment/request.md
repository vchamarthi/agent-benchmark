# End-user request

Can I use mkl_random to speed up this sampler?

```python
import numpy as np

def draw_samples(seed, n):
    rng = np.random.default_rng(seed)
    a = rng.standard_normal(n)
    b = rng.integers(0, 100, size=n)
    return a, b
```
