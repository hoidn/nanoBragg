## 2025-09-30
- Reviewed current repo state; no prior galph memory.
- Identified critical outstanding parity failures (AT-020/021/022/024). AT-021 phi rotation bug is root cause for AT-022.
- Per long-term goals, PyTorch still shows major parity gaps plus performance overhead (torch.compile warm-up dominates small detectors; large crystal case still ~7× slower vs C). Potential optimizations: share compiled kernels across instances, real geometry caching, consider chunked evaluation to trim memory.
- Created supervisor plan for AT-021 debugging at `plans/active/at-parallel-021/plan.md`; cross-referenced from fix_plan. This plan should be the next loop (requires prompts/debug.md).
- Observed Ralph’s recent loops mainly documentation/perf; no regressions but backlog untouched. Next action for Ralph: run debug loop against AT-021 using new plan.
