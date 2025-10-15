# Phase J Guardrails — Open Questions

## Infrastructure Fixture (Task J1)

### Q1: Binary Version Tracking
**Question:** Should the session fixture capture and log the C binary SHA256 hash at session start for traceability?

**Context:** Would help diagnose issues caused by silent binary updates between test runs, but adds ~0.1s overhead per session.

**Options:**
1. **Yes, always track:** Compute SHA256 and log to `reports/test_run_<timestamp>/c_binary_hash.txt`
2. **Optional via env var:** Only track if `NB_LOG_BINARY_HASH=1`
3. **No, defer:** Current Phase H artifact captures are sufficient

**Recommendation:** Option 2 (optional via env var) — provides debugging capability without imposing overhead on fast test iterations.

**Owner:** Implementation loop (next)
**Blocking:** No — can be added post-Phase J if needed

---

### Q2: Golden Asset Staleness Warnings
**Question:** Should fixtures warn if golden assets are >30 days old?

**Context:** Stale assets might indicate outdated test environment, but legitimate long-lived assets (like `scaled.hkl`) could trigger false positives.

**Options:**
1. **Yes, warn on stale:** Emit UserWarning if asset mtime > 30 days
2. **CI-only check:** Only warn in CI environment (detect via `CI=true` env var)
3. **No, rely on hash checks:** Phase H hash validation is sufficient

**Recommendation:** Option 3 (no staleness checks) — Asset correctness validated by hashes in Phase H; mtime is not a reliable indicator of correctness.

**Owner:** Documentation/process improvement (if recurring issues emerge)
**Blocking:** No

---

### Q3: NB_C_BIN Precedence Documentation
**Question:** Should fixture emit a warning when falling back to default paths instead of explicit `NB_C_BIN`?

**Context:** Explicit `NB_C_BIN` is best practice per `docs/development/c_to_pytorch_config_map.md`, but many users rely on fallbacks successfully.

**Options:**
1. **Yes, always warn:** Emit UserWarning on fallback usage
2. **CI-only warning:** Only warn in CI to encourage explicit configuration
3. **No warning, document only:** Keep fallback silent, document in testing strategy

**Recommendation:** Option 3 (no warning) — Fallback behavior is well-defined and documented; warnings would create noise without clear benefit.

**Owner:** Documentation (testing_strategy.md already documents precedence)
**Blocking:** No

---

### Q4: Fixture Failure Logging
**Question:** Should infrastructure gate failures be logged to a separate file for CI/CD diagnostics?

**Context:** pytest's built-in failure reporting is comprehensive, but separate log file might simplify CI artifact collection.

**Options:**
1. **Yes, log to `reports/infrastructure_failures.log`:** Append failures with timestamps
2. **CI-only logging:** Only create separate log in CI environment
3. **No, rely on pytest output:** pytest's built-in reporting is sufficient

**Recommendation:** Option 3 (rely on pytest) — pytest output is already captured by CI systems, and separate logging adds complexity without clear value.

**Owner:** CI/CD integration (if CI tooling requires specific artifact format)
**Blocking:** No

---

### Q5: Fixture Validation Testing
**Question:** How should we test the fixtures themselves? Create synthetic test environment with missing binaries/assets to verify failure messages?

**Context:** Validation plan (Task J3) addresses this, but implementation details are open.

**Options:**
1. **Manual synthetic scenarios:** Temporarily rename binaries/assets, run pytest, verify messages (as specified in validation_plan.md V2-V4)
2. **Automated test script:** Create `scripts/validation/test_fixtures.sh` with teardown/restore logic
3. **Dedicated pytest fixture tests:** Create `tests/test_fixtures.py` with monkeypatch for synthetic failures

**Recommendation:** Option 1 (manual validation) for Phase J evidence-only; Option 3 (dedicated pytest tests) for long-term regression prevention after implementation.

**Owner:** Implementation loop (manual) + test suite enhancement (future)
**Blocking:** No — manual validation sufficient for Phase J

---

## Gradient Policy Fixture (Task J2)

### Q6: CI Enforcement Strategy
**Question:** Should CI jobs fail hard if gradient tests are skipped due to missing `NANOBRAGG_DISABLE_COMPILE=1`?

**Context:** Prevents accidental skips in automated runs, but may complicate multi-job CI pipelines where not all jobs run gradient tests.

**Options:**
1. **Yes, fail on skip:** Add pytest plugin or post-test check to detect skipped gradient tests and fail CI
2. **Gradient-specific CI job:** Create dedicated CI job with explicit environment, let other jobs skip
3. **No enforcement, rely on skip visibility:** Trust developers to notice skip messages

**Recommendation:** Option 2 (dedicated CI job) — Cleanly separates gradient validation from general test suite, allows explicit environment setup without complicating other jobs.

**Owner:** CI/CD integration (post-Phase K)
**Blocking:** No — fixture works correctly regardless of CI enforcement

---

### Q7: Fixture Scope Optimization
**Question:** Could we use `session` scope instead of `module` if gradient tests expand to multiple files?

**Context:** Currently `test_gradients.py` is single module. If gradient tests grow to `test_gradients_*.py` pattern, session scope would be more appropriate.

**Options:**
1. **Yes, use session scope now:** Anticipate future expansion
2. **Module scope now, refactor later:** Keep simple for single-file case, refactor when multi-file structure emerges
3. **Session scope in conftest.py:** Move gradient guard to `tests/conftest.py` as session-scoped fixture

**Recommendation:** Option 2 (module scope for now) — YAGNI principle. Refactor if/when multi-file gradient tests are added.

**Owner:** Future gradient test expansion (if needed)
**Blocking:** No

---

### Q8: Environment Variable Naming
**Question:** Is `NANOBRAGG_DISABLE_COMPILE` sufficiently descriptive? Alternative: `NANOBRAGG_GRADCHECK_MODE=1`?

**Context:** Current name aligns with simulator flag, but alternative might be clearer to users.

**Options:**
1. **Keep current:** `NANOBRAGG_DISABLE_COMPILE` (consistency with simulator)
2. **Rename to:** `NANOBRAGG_GRADCHECK_MODE` (clarity of purpose)
3. **Support both:** Accept either variable, prefer `GRADCHECK_MODE`

**Recommendation:** Option 1 (keep current) — Variable name matches underlying simulator behavior, and renaming would break existing workflows (Phase M2 validation uses current name).

**Owner:** None (resolved — keep current naming)
**Blocking:** No

---

### Q9: Logging Integration
**Question:** Should gradient policy guard log when tests are skipped to `reports/` for audit trail?

**Context:** Could help diagnose cases where users are confused about why gradient tests didn't run.

**Options:**
1. **Yes, log skips:** Append to `reports/gradient_test_skips.log` with timestamp
2. **CI-only logging:** Only log in CI environment
3. **No logging:** pytest skip output is sufficient

**Recommendation:** Option 3 (no logging) — pytest's skip reporting with `-v` flag provides adequate visibility. Additional logging adds complexity without clear benefit.

**Owner:** None (resolved — skip additional logging)
**Blocking:** No

---

### Q10: Phase I Timeout Interaction
**Question:** Phase I established 905s timeout for `test_property_gradient_stability`. Should gradient policy fixture verify timeout marker is present?

**Context:** Could catch accidental removal of `@pytest.mark.timeout(905)`, but adds coupling between fixtures.

**Options:**
1. **Yes, verify timeout marker:** Check for marker presence during fixture setup
2. **No, rely on pytest-timeout plugin:** Plugin will handle missing markers gracefully
3. **Separate fixture for timeout policy:** Create dedicated fixture for timeout enforcement

**Recommendation:** Option 2 (rely on pytest-timeout) — Timeout enforcement is pytest-timeout's responsibility. Gradient policy guard should remain focused on compile guard only (single responsibility principle).

**Owner:** None (resolved — out of scope for policy guard)
**Blocking:** No

---

## Validation Strategy (Task J3)

### Q11: Validation Frequency
**Question:** Should fixture validation be added to CI as a pre-test gate?

**Context:** Adds ~1 minute overhead but prevents fixture regressions. Trade-off between CI time and regression safety.

**Options:**
1. **Yes, run validation on every CI run:** Add as mandatory gate before test execution
2. **Scheduled validation:** Run fixture validation nightly or weekly, not per-commit
3. **Manual validation only:** Run validation when fixtures are modified, not on every commit

**Recommendation:** Option 3 (manual validation) initially, upgrade to Option 2 (scheduled) if fixture regressions occur. Option 1 is overkill for stable fixtures.

**Owner:** CI/CD integration (post-Phase K if regressions observed)
**Blocking:** No

---

### Q12: Artifact Retention
**Question:** How long should validation logs be retained?

**Context:** Validation logs are ~50KB per STAMP. Balance between disk usage and historical debugging capability.

**Options:**
1. **Indefinite retention:** Keep all validation artifacts forever
2. **Archive after completion:** Move to `archive/` after corresponding phase completes
3. **Time-based cleanup:** Delete validation logs >90 days old

**Recommendation:** Option 2 (archive after completion) — Move Phase J artifacts to `reports/archive/phase_j_20251015T180301Z/` after Phase K validates that fixtures work in full suite.

**Owner:** Documentation maintenance (post-Phase K)
**Blocking:** No

---

### Q13: Fixture Evolution
**Question:** When fixture logic changes, should validation be re-run?

**Context:** Establishes process for fixture maintenance and regression prevention.

**Options:**
1. **Yes, always re-validate:** Run V1-V9 suite after any fixture change
2. **Validation for non-trivial changes only:** Skip validation for comment/docstring edits
3. **No formal policy:** Developer discretion

**Recommendation:** Option 1 (always re-validate) — Validation is cheap (~5 minutes) and provides high confidence. Should be part of standard fixture update workflow.

**Owner:** Development process (document in testing_strategy.md)
**Blocking:** No

---

### Q14: Phase K Trigger Condition
**Question:** Should Phase K (full suite rerun) wait for stakeholder sign-off on Phase J deliverables?

**Context:** Ensures fixture designs are reviewed before implementation investment begins.

**Options:**
1. **Yes, require sign-off:** Stakeholder reviews J1/J2/J3 docs, approves before implementation
2. **Async review:** Begin implementation, incorporate feedback in Phase K
3. **No review gate:** Trust executor judgment, proceed to implementation

**Recommendation:** Option 1 (require sign-off) — Phase J is evidence-only by design. Stakeholder review ensures fixture designs align with project needs before implementation loop begins.

**Owner:** Supervisor/galph (sign-off provider)
**Blocking:** **YES** — Implementation should wait for explicit approval of Phase J deliverables

---

## Summary of Blocking Questions

**Critical (Must Resolve Before Implementation):**
- **Q14:** Phase K trigger condition (requires stakeholder sign-off) — ✅ Resolved 2025-10-15T18:55Z by galph; implementation may proceed per Phase K plan.

**Non-Blocking (Can Defer):**
- Q1-Q13: All other questions have recommendations and can be revisited if issues emerge

## Next Steps

1. **Immediate:** Present Phase J deliverables (J1/J2/J3 docs) to stakeholder for review
2. **Upon Approval:** Proceed to implementation loop (fixtures + validation)
3. **Post-Validation:** Update this document with resolution notes for any questions that surfaced during implementation

## References

- **Fixture Designs:** `analysis/session_fixture_design.md`, `analysis/gradient_policy_guard.md`
- **Validation Plan:** `analysis/validation_plan.md`
- **Plan Context:** `plans/active/test-suite-triage-phase-h.md` Phase J tasks
