### **Bug Report: `C-PARITY-001`**

**Title:** Stale Crystal Vector State Carryover in `nanoBragg.c` at φ=0

**Date Reported:** 2025-10-07

**Discovered By:** Agent `ralph` (during `CLI-FLAGS-003` parity analysis, Attempt #101)

**Severity:** `Medium` (Causes numerical deviation and parity failures, but does not crash)

**Priority:**
*   **For PyTorch Parity:** `High` (Must be addressed to unblock supervisor command validation)
*   **For C Codebase:** `Low` (Long-standing behavior; fix is optional but recommended for physical correctness)

---

### **1. Summary**

The reference `nanoBragg.c` implementation fails to correctly initialize crystal orientation vectors at the start of each per-pixel `phi` oscillation loop. When the first `phi` step (`phi_tic=0`) has a rotation angle of exactly `0.0`, the code skips the rotation logic but does not reset the working orientation vectors. This causes these vectors to retain their values from the final `phi` step of the *previous pixel*, leading to an incorrect calculation for the first oscillation step of every subsequent pixel.

This behavior breaks parity with the physically correct PyTorch implementation and was the root cause of the persistent `k_frac` mismatch and Verification Gate failures (VG-1, VG-3) in the `CLI-FLAGS-003` initiative.

### **2. Steps to Reproduce**

1.  **Instrument `nanoBragg.c`:** Add `printf` statements within the `phi_tic` loop (around line 3060) to trace the values of `phi_tic`, `phi` (angle), the rotated vectors (`ap`, `bp`, `cp`), and the derived Miller indices (`h`, `k`, `l`). An example is the `TRACE_C_PHI` instrumentation from Attempt #101.
2.  **Rebuild the C Binary:** Run `make -C golden_suite_generator`.
3.  **Execute a Trace Run:** Run the instrumented C binary with the full supervisor command and the `-trace_pixel` flag for any pixel (e.g., `685 1039`).
    ```bash
    ./golden_suite_generator/nanoBragg -mat A.mat ... -phi 0 -osc 0.1 -phisteps 10 -trace_pixel 685 1039 > c_trace.log
    ```
4.  **Examine the Output:** In the `c_trace.log`, observe the `TRACE_C_PHI` lines for `phi_tic=0` and `phi_tic=9`.

### **3. Expected Behavior**

When `phi_tic=0`, the rotation angle `phi` is 0.0. The `rotate_axis` function should effectively be an identity operation. The rotated vectors (`ap`, `bp`, `cp`) should be identical to the initial, un-rotated base vectors (`a0`, `b0`, `c0`) for the current pixel. Consequently, the `k_frac` value for `phi_tic=0` should be calculated based on this un-rotated orientation.

### **4. Actual Behavior**

The C code's `phi` rotation is guarded by an `if (phi != 0.0)` condition.
*   At `phi_tic=0`, `phi` is `0.0`, so the rotation is skipped.
*   The working vectors (`ap`, `bp`, `cp`) are **not reset** to their base state (`a0`, `b0`, `c0`).
*   They retain their values from the end of the previous pixel's loop (i.e., from when `phi_tic=9`).

This is proven by the trace output, where the values for `phi_tic=0` are identical to the values from `phi_tic=9`, which is physically incorrect.

**Evidence from `c_trace_phi_202510070839.log`:**
```
TRACE_C_PHI phi_tic=0 phi_deg=0 k_frac=-0.607255839576692 ...
...
TRACE_C_PHI phi_tic=9 phi_deg=0.09 k_frac=-0.607255839576692 ...
```
The `k_frac` values are identical, demonstrating the stale state was used for the `phi_tic=0` calculation.

### **5. Root Cause Analysis (RCA)**

The bug is located in the main simulation loop of `golden_suite_generator/nanoBragg.c`. The working vectors `ap`, `bp`, `cp` are declared at a scope outside the `phi_tic` loop. Inside the loop, the rotation logic is:

```c
/* from nanoBragg.c, around line 3055 */
phi = phi0 + phistep*phi_tic;
if( phi != 0.0 )
{
    rotate_axis(a0,ap,spindle_vector,phi);
    rotate_axis(b0,bp,spindle_vector,phi);
    rotate_axis(c0,cp,spindle_vector,phi);
}
/* No 'else' block to handle the phi == 0.0 case */
```

Because there is no `else` block to handle the `phi == 0.0` case, `ap`, `bp`, and `cp` are never reset to `a0`, `b0`, and `c0` at the start of the loop, leading to the state carryover.

### **6. Impact on PyTorch Parity**

The PyTorch implementation correctly calculates a zero rotation for `phi_tic=0`, resulting in the use of the un-rotated base vectors. This "correct" behavior causes a parity failure against the "buggy" C reference. The primary project goal is **translation correctness**, which requires emulating the reference C behavior, including its bugs.

An attempt to "fix" the PyTorch-side test to match its own correct output (Attempt #102) was correctly identified as an invalid regression that masked the parity gap.

### **7. Recommended Action**

1.  **Short-Term (PyTorch Project):** The PyTorch implementation of `Crystal.get_rotated_real_vectors` must be modified to **emulate** the C code's buggy behavior. This likely involves adding a special condition that, for `phi_tic=0`, it uses the vector state from the final `phi` step. This will allow the `CLI-FLAGS-003` initiative to achieve parity and unblock the long-term goal. The `pytest` assertions in `tests/test_cli_scaling_phi0.py` must be restored to expect the buggy C values to guide this fix (TDD).

2.  **Long-Term (C Code Maintenance):** This report should be logged as a known issue in the `nanoBragg.c` codebase. A future version of `nanoBragg.c` should fix this by adding an `else` block to reset the `ap, bp, cp` vectors before the `phi_tic=0` calculation.
    ```c
    else
    {
        ap[1]=a0[1]; ap[2]=a0[2]; ap[3]=a0[3];
        bp[1]=b0[1]; bp[2]=b0[2]; bp[3]=b0[3];
        cp[1]=c0[1]; cp[2]=c0[2]; cp[3]=c0[3];
    }
    ```
