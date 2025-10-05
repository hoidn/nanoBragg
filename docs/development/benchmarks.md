# Microbenchmarks for Physics Helpers

Run helper benchmarks in both float64 (dev) and float32 (prod), on CPU and GPU as applicable.

Goals:
- Detect regressions in hot paths (e.g., `sincg`, `sinc3`, polarization)
- Compare minimal vs over-hardened versions before merging

Example skeleton (Python):

```
# scripts/benchmarks/benchmark_sinc_helpers.py
import torch, time

@torch.inference_mode()
def bench(fn, u, N, iters=20):
    # Warmup
    for _ in range(5): fn(u, N)
    times = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn(u, N)
        if u.is_cuda: torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)
    times.sort()
    k = max(1, iters//10)
    return sum(times[k:-k]) / max(1, iters - 2*k)  # trimmed mean

# Generate inputs near and far from nπ
n = 1_000_000
u = torch.pi * (torch.rand(n, dtype=torch.float32) - 0.5)  # [-0.5π, 0.5π]
N = torch.tensor(5.0, dtype=u.dtype)

# time it
print("sincg time:", bench(sincg, u, N))
```

Acceptance threshold:
- ±5% time change for “no-behavior-change” patches
- Otherwise, include justification and downstream perf impact
