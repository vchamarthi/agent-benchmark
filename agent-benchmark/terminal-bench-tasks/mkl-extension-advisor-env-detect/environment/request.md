# End-user request

I think numpy on this machine already uses MKL for FFT but I'm not sure. Here's my code, should I add any patches?

```python
import numpy as np
y = np.fft.fft(my_signal)
```
