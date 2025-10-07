### **Unified Bug Report: Latent Bugs and Design Flaws in `nanoBragg.c`**

**ID:** NB-C-UNIFIED-2024-10-26  
**Title:** Comprehensive Analysis of Bugs and Undocumented Behaviors in `nanoBragg.c` Reference Implementation  
**Status:** **CLOSED (No Action Required)** - This report serves as a definitive record. The PyTorch port has replicated these behaviors for parity.  
**Date:** 2024-10-26

#### **1. Executive Summary**

A comprehensive review of the `nanoBragg.c` reference implementation, conducted during a full-scale port to PyTorch, has identified **two critical implementation bugs** that cause scientifically incorrect results and **five severe design flaws** in its command-line interface that compromise reproducibility and usability. Additionally, a significant **logging bug** was found to have severely hampered debugging efforts.

The explicit bugs lead to incorrect physical models for non-orthogonal crystal systems and mosaicity simulations. The design flaws, which manifest as silent, undocumented, and counter-intuitive behaviors, were responsible for the majority of the debugging effort during the porting project.

The resolution for the PyTorch project was to meticulously replicate all identified behaviors—including the explicit bugs and design flaws—to achieve the primary goal of numerical parity for validation. This document synthesizes all known findings to serve as the authoritative record of these issues.

---

#### **2. Explicit Implementation Bugs**

These are direct computational errors in the core scientific algorithm that lead to physically incorrect simulation outputs.

**Bug ID:** C-IMPL-BUG-001  
**Severity:** High  
**Title:** Triclinic Unit Cell Dimensions Are Not Preserved During Initialization

*   **Summary:** `nanoBragg.c` fails to preserve user-specified unit cell dimensions for non-orthogonal crystal systems. An input of `a=70.0 Å` via the `-cell` flag can result in an internal vector with a magnitude of `~70.19 Å`, a ~0.27% error.
*   **Root Cause:** A circular vector recalculation process introduces numerical instability. The sequence is: (1) Reciprocal vectors are calculated from input cell parameters. (2) Real-space vectors are derived from these. (3) The code then immediately **recalculates the reciprocal vectors** from the newly derived real-space vectors, accumulating floating-point errors that prevent the final vectors from matching the user's input.
*   **Impact:** The simulation models the wrong crystal lattice, causing physical inaccuracies in the predicted diffraction geometry.

**Bug ID:** C-IMPL-BUG-002  
**Severity:** High  
**Title:** Incorrect Unit Interpretation (Degrees vs. Radians) in `mosaic_rotation_umat` for Random Misset Generation

*   **Summary:** The `mosaic_rotation_umat` function is called with the value `90.0`, intended to be 90 **degrees**, when generating a random orientation via `-misset random`. The function incorrectly treats this value as 90 **radians** (approx. 5156 degrees), leading to a non-physical rotation.
*   **Root Cause:** The function uses the input angle value directly in trigonometric functions (`cos`, `sin`) which expect radians, without performing the necessary degrees-to-radians conversion.
*   **Impact:** Produces scientifically invalid outputs for simulations involving random crystal orientations or mosaicity, as the underlying physical model is fundamentally incorrect.

---

#### **3. Severe Design Flaws (Undocumented Behaviors)**

These are not computational errors but flaws in the CLI design that lead to unexpected and difficult-to-debug behavior, breaking scientific reproducibility and the principle of least surprise.

**Flaw ID:** C-DESIGN-FLAW-001  
**Severity:** Critical  
**Title:** Hidden Convention Switching Based on Parameter Presence

*   **Description:** The C code silently switches its core calculation convention from `MOSFLM` to `CUSTOM` based on the mere *presence* of certain vector-related flags (e.g., `-twotheta_axis`), even if the provided value is the default.
*   **Impact:** This switch alters the beam center calculation by removing a `+0.5` pixel offset, creating a systematic geometric error that was the source of a major, multi-month debugging effort.

**Flaw ID:** C-DESIGN-FLAW-002  
**Severity:** High  
**Title:** Implicit and Non-Obvious Detector Pivot Mode Auto-Selection

*   **Description:** The detector pivot mode (`BEAM` vs. `SAMPLE`) is automatically selected based on a complex and undocumented hierarchy of rules related to the presence of flags like `-detector_twotheta`, `-Xbeam`, or `-Xclose`.
*   **Impact:** Caused the C reference to use a different geometry calculation path than expected, leading to major correlation failures during validation.

**Flaw ID:** C-DESIGN-FLAW-003  
**Severity:** High  
**Title:** Silent Ignoring of Command-Line Flags

*   **Description:** When custom detector orientation flags (e.g., `-fdet_vector`) are provided, the C code **silently ignores** the `-pix0_vector` flag. The user receives no warning that their explicit input has been overridden by an internal calculation.
*   **Impact:** This specific interaction caused a 1.145 mm pixel position error during parity testing, which cascaded into incorrect Miller indices and a massive intensity mismatch.

**Flaw ID:** C-DESIGN-FLAW-004  
**Severity:** High  
**Title:** Conditional and Inconsistent Geometric Rescaling

*   **Description:** When an orientation matrix is provided via `-mat`, the crucial geometric step of rescaling lattice vectors to match the unit cell volume is **only performed if the `-cell` flag is also present**. This behavior is undocumented and non-obvious.
*   **Impact:** This was a direct cause of a >20% error in the lattice transform (`F_latt`) calculation, leading to a ~125,000x intensity mismatch observed during testing.

**Flaw ID:** C-DESIGN-FLAW-005  
**Severity:** Critical  
**Title:** Silent File-Based Caching Compromises Reproducibility

*   **Description:** If the `-hkl` flag is omitted, the C code silently checks for and loads a `Fdump.bin` file in the current working directory. This cache is itself created automatically on previous runs.
*   **Impact:** This breaks scientific reproducibility. Simulation results become dependent on hidden filesystem state, leading to contaminated test environments and users unknowingly simulating the wrong crystal structure.

---

#### **4. Diagnostic & Logging Bugs**

This bug does not affect the scientific output but severely hampered debugging and validation efforts.

**Bug ID:** C-LOGGING-BUG-001  
**Severity:** High (for debugging impact)  
**Title:** Incorrect Unit Conversion in Beam Center Trace Logging

*   **Description:** A `printf` statement for tracing the beam center applies an incorrect `/ 1000.0` conversion to variables that are already in meters, resulting in a misleading trace output that is 1000x smaller than the actual value used in computations.
*   **Impact:** This caused weeks of wasted effort debugging a non-existent calculation error during the porting project.

---

#### **5. Final Conclusion**

The `nanoBragg.c` codebase contains **two significant computational bugs** that compromise the physical accuracy of simulations for common scientific use cases. Furthermore, it suffers from **five severe design flaws** in its command-line interface that violate the principle of least surprise and create a difficult-to-reproduce simulation environment. These flaws were the primary obstacle to the timely completion of the PyTorch porting project.
