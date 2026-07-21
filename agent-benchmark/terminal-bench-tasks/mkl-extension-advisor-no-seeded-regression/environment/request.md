# End-user request

We want this faster but the test below must keep passing. Can mkl_random help?

```python
import numpy as np

def test_pricer_regression():
    np.random.seed(0)
    shocks = np.random.standard_normal(1_000_000)
    price = run_pricer(shocks)
    assert abs(price - 100.4237) < 1e-4   # golden value
```
