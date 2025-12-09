"""
Runtime cache for compiled kernels.

Implements shared cache for torch.compile'd functions to avoid
recompilation overhead across Simulator instances with matching
runtime parameters.

Design per PERF-PYTORCH-004 Phase 2.1:
- Module-level singleton for simplicity
- Cache key: (device, dtype, oversample, n_sources)
- Thread-safe via simple locking (future extension if needed)
- Explicit invalidation when cache grows too large
"""

from typing import Optional, Tuple, Callable
import torch


class CompiledKernelCache:
    """
    Cache for compiled physics kernels.

    Each simulator instance with matching runtime parameters can reuse
    the same compiled kernel, avoiding 0.5-6s compilation overhead.
    """

    def __init__(self, max_entries: int = 50):
        """
        Initialize cache.

        Args:
            max_entries: Maximum number of compiled kernels to cache.
                When exceeded, the entire cache is cleared (simple LRU alternative).
        """
        self._cache = {}
        self._max_entries = max_entries
        self._hits = 0
        self._misses = 0

    def _make_key(
        self,
        device: torch.device,
        dtype: torch.dtype,
        oversample: int,
        n_sources: int
    ) -> Tuple:
        """
        Generate cache key from runtime parameters.

        Args:
            device: PyTorch device (cpu/cuda:0/etc)
            dtype: PyTorch data type (float32/float64)
            oversample: Subpixel grid size
            n_sources: Number of beam sources (divergence/dispersion)

        Returns:
            Tuple suitable for dict key
        """
        # Normalize device to ensure 'cuda:0' and 'cuda' match
        device_str = str(device)
        if device.type == 'cuda' and device.index is None:
            device_str = f'cuda:0'

        return (device_str, dtype, oversample, n_sources)

    def get(
        self,
        device: torch.device,
        dtype: torch.dtype,
        oversample: int,
        n_sources: int
    ) -> Optional[Callable]:
        """
        Retrieve compiled kernel from cache.

        Args:
            device: PyTorch device
            dtype: PyTorch data type
            oversample: Subpixel grid size
            n_sources: Number of beam sources

        Returns:
            Compiled function if found, None otherwise
        """
        key = self._make_key(device, dtype, oversample, n_sources)
        compiled_fn = self._cache.get(key)

        if compiled_fn is not None:
            self._hits += 1
        else:
            self._misses += 1

        return compiled_fn

    def put(
        self,
        device: torch.device,
        dtype: torch.dtype,
        oversample: int,
        n_sources: int,
        compiled_fn: Callable
    ):
        """
        Store compiled kernel in cache.

        Args:
            device: PyTorch device
            dtype: PyTorch data type
            oversample: Subpixel grid size
            n_sources: Number of beam sources
            compiled_fn: Compiled function to cache
        """
        # Simple eviction: clear entire cache when too large
        if len(self._cache) >= self._max_entries:
            self._cache.clear()

        key = self._make_key(device, dtype, oversample, n_sources)
        self._cache[key] = compiled_fn

    def clear(self):
        """Clear all cached kernels."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with hits, misses, and hit rate
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
            'size': len(self._cache)
        }


# Global singleton cache
_global_kernel_cache = CompiledKernelCache()


def get_global_kernel_cache() -> CompiledKernelCache:
    """Get the global compiled kernel cache."""
    return _global_kernel_cache


def clear_global_cache():
    """Clear the global kernel cache."""
    _global_kernel_cache.clear()
