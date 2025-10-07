### **Unified Bug Report: `nanoBragg` CLI Conventions**

This report synthesizes findings from the `CLI-FLAGS-003` investigation, detailing two critical, related bugs in the `nanoBragg.c` command-line interface that lead to silent scientific invalidity and extreme difficulty in achieving parity.

---

### **Bug 1: NANO-C-BUG-001 - Silent Unit Mismatch in `-pix0_vector_mm` Flag**

**Title:** Silent Unit Mismatch in `-pix0_vector_mm` Flag Leads to 1000x Error in Detector Geometry

**Severity:** **Critical**
**Date Found:** 2025-10-05

#### **1. Summary**

The `nanoBragg` C binary incorrectly parses the `-pix0_vector_mm` command-line flag. Although the `_mm` suffix implies the input values are in millimeters, the program silently interprets them as meters. This results in a 1000x error in the placement of the detector origin (`pix0_vector`), leading to the generation of scientifically invalid diffraction data without any warning to the user.

#### **2. Root Cause & Evidence**

The issue stems from the argument parsing logic in `nanoBragg.c` (approx. line 740). The code uses `strstr(argv[i], "-pix0_vector")` to detect both `-pix0_vector` and `-pix0_vector_mm` flags. However, the subsequent code block does not differentiate between the two variants. It unconditionally calls `atof()` to parse the values and assigns them directly to the `pix0_vector` array, which is assumed to be in meters.

This was discovered during Phase A of the `CLI-FLAGS-003` plan, with evidence captured in `reports/2025-10-cli-flags/phase_a/README.md` and `reports/2025-10-cli-flags/phase_a/pix0_trace/trace.log`.

#### **3. Impact & Suggested Fix**

This is a critical scientific validity bug. The failure is silent, giving no indication of misinterpretation. The recommended fix is to modify the parsing logic to first check for the more specific `_mm` suffix, apply a `0.001` scaling factor if found, and then fall back to checking for the meter-based `-pix0_vector` flag.

---

### **Bug 2: NANO-C-BUG-002 - Undocumented Override Precedence with Custom Vectors**

**Title:** Undocumented Precedence Logic for `-pix0_vector_mm` Silently Overrides `Xbeam`/`Ybeam` When Custom Detector Vectors are Present

**Severity:** **High** (for parity/reimplementation), **Medium** (for users)
**Date Found:** 2025-10-21 (Corrected from an earlier, flawed analysis)

#### **1. Summary**

The C implementation contains non-obvious precedence logic for handling detector geometry. When custom detector vectors (e.g., `-fdet_vector`) are supplied, one might assume that the `-pix0_vector_mm` flag would be ignored, as the geometry is fully defined. Instead, the C code uses the `-pix0_vector_mm` value to **recalculate** the internal `Fbeam` and `Sbeam` parameters, effectively overriding the values derived from `-Xbeam` and `-Ybeam`. This undocumented behavior makes the code's logic extremely difficult to replicate and led to a prolonged debugging effort.

#### **2. Description & Root Cause**

This issue was the primary driver of the massive **124,538x intensity mismatch** observed during the agent's parity tests. The PyTorch implementation was written based on the logical assumption that custom vectors would cause the `pix0_vector` override to be ignored.

The agent's investigation initially produced conflicting evidence:
1.  An early analysis (Attempt #23, based on flawed instrumentation) incorrectly concluded the override was ignored.
2.  A deeper analysis (Phase J/H5, see `docs/fix_plan.md` Attempts #28/#29) proved this was wrong. The C code indeed uses the override to recalculate `Fbeam`/`Sbeam`, which then alters the final `pix0_vector` and cascades into a completely different `F_latt` value, explaining the intensity error.

The root cause is an implicit design choice in the C code where `-pix0_vector_mm` acts as a high-precedence method for defining the beam center, even when other conflicting parameters are present.

#### **3. Impact**

This is a critical **reproducibility and validation bug**. It makes achieving 1:1 parity with the C code nearly impossible without extensive, pixel-level reverse engineering. The agent spent multiple iterations correcting its PyTorch implementation (`Detector._calculate_pix0_vector`) due to this non-obvious behavior. Any team attempting to validate or reimplement `nanoBragg` would face the same significant hurdle.

#### **4. Suggested Fix**

The C code's calculation is not necessarily "wrong," but its behavior is undocumented and counter-intuitive. The suggested fix is to:
1.  Add extensive comments in `nanoBragg.c` (approx. lines 1830-1860) explaining that `-pix0_vector_mm` is used to re-derive `Fbeam`/`Sbeam` and thus overrides `-Xbeam`/`-Ybeam`, even if custom detector vectors are present.
2.  Consider adding a CLI warning to the user when both `-Xbeam`/`-Ybeam` and `-pix0_vector_mm` are supplied, informing them which value is taking precedence.

#### **5. Evidence**
*   **Initial Parity Failure:** `reports/2025-10-cli-flags/phase_i/supervisor_command/README.md`
*   **Corrected C-Code Behavior:** `reports/2025-10-cli-flags/phase_h5/c_precedence.md`
*   **Agent's Implementation Fix:** Commit `c0be084`, `5878f16`.
