# Manual sincg reproduction

- Run directory: reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z
- Py trace: reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/trace_py_scaling.log
- C trace: /home/ollie/Documents/tmp/nanoBragg/reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log
- Na, Nb, Nc = (36, 47, 29)

| Axis | frac | rounded | sincg(π·frac) | sincg(π·(frac-h0)) | C trace | Py trace |
| --- | --- | --- | --- | --- | --- | --- |
| a | -6.879534963 | -7 | -2.358241334 | 2.358241334 | -2.360127360 | -2.358195120 |
| b | -0.607262621 | -1 | 1.050667596 | 1.050667596 | 1.050796643 | 1.050667393 |
| c | -13.766295239 | -14 | 0.960608070 | 0.960608070 | 0.960961004 | 0.960630659 |

- Product using sincg(π·frac): -2.380125274
- Product using sincg(π·(frac-h0)): 2.380125274
- C trace F_latt: -2.383196653
- Py trace F_latt: -2.380134142

Interpretation:
- Compare the C trace columns to identify which sincg flavour matches.
- Use these values when drafting `lattice_hypotheses.md`.
