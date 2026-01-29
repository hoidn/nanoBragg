"""
KL weight annealing schedule for β-VAE style ELBO rebalancing.

Provides a linear warmup schedule that ramps the KL weight (β) from a
low starting value to 1.0 over a configurable number of warmup steps,
preventing posterior collapse in early VI training.

Reference: docs/plans/2026-01-29-vi-elbo-balancing.md Task 2
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LinearKLWeightSchedule:
    """Linear KL weight annealing from ``start`` to ``end`` over ``warmup_steps``.

    After ``warmup_steps`` iterations the weight clamps to ``end``.

    >>> sched = LinearKLWeightSchedule(start=0.1, end=1.0, warmup_steps=50)
    >>> sched.weight(step=0)
    0.1
    >>> sched.weight(step=50)
    1.0
    """

    start: float = 0.1
    end: float = 1.0
    warmup_steps: int = 50

    def weight(self, step: int, total_iters: int | None = None) -> float:
        """Return the KL weight for the given training step.

        Args:
            step: Current iteration (0-indexed).
            total_iters: Total iterations (unused, reserved for future
                non-linear schedules).

        Returns:
            KL weight β clamped to [start, end].
        """
        if self.warmup_steps <= 0:
            return self.end
        t = min(step / self.warmup_steps, 1.0)
        return self.start + (self.end - self.start) * t
