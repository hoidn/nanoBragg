#!/bin/bash
# M2d cross-pixel carryover probe
# Runs trace harness for two consecutive pixels to gather evidence of φ carryover behavior
set -e

RUN_DIR="reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T100653Z/carryover_probe"

echo "=== Running M2d Cross-Pixel Carryover Probe ===" | tee "$RUN_DIR/commands.txt"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$RUN_DIR/commands.txt"
echo "Git SHA: $(git rev-parse HEAD)" | tee -a "$RUN_DIR/commands.txt"
echo "" | tee -a "$RUN_DIR/commands.txt"

# Pixel 1: 684, 1039
echo "### Pixel 1 (684, 1039) ###" | tee -a "$RUN_DIR/commands.txt"
CMD1="KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 684 1039 --config supervisor --dtype float64 --phi-mode c-parity --emit-rot-stars --out $RUN_DIR/trace_pixel1.log"
echo "$CMD1" | tee -a "$RUN_DIR/commands.txt"
eval "$CMD1" 2>&1 | tee "$RUN_DIR/pixel1_stdout.log"
echo "Exit code: $?" | tee -a "$RUN_DIR/commands.txt"
echo "" | tee -a "$RUN_DIR/commands.txt"

# Pixel 2: 685, 1039
echo "### Pixel 2 (685, 1039) ###" | tee -a "$RUN_DIR/commands.txt"
CMD2="KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --dtype float64 --phi-mode c-parity --emit-rot-stars --out $RUN_DIR/trace_pixel2.log"
echo "$CMD2" | tee -a "$RUN_DIR/commands.txt"
eval "$CMD2" 2>&1 | tee "$RUN_DIR/pixel2_stdout.log"
echo "Exit code: $?" | tee -a "$RUN_DIR/commands.txt"
echo "" | tee -a "$RUN_DIR/commands.txt"

# Capture environment
python -c "import sys, torch, platform; import json; print(json.dumps({'python': sys.version, 'torch': torch.__version__, 'platform': platform.platform()}, indent=2))" > "$RUN_DIR/env.json"

# Generate SHA256 checksums
cd "$RUN_DIR"
sha256sum *.log *.txt *.json *.sh > sha256.txt 2>/dev/null || true
cd - > /dev/null

echo "" | tee -a "$RUN_DIR/commands.txt"
echo "=== Probe Complete ===" | tee -a "$RUN_DIR/commands.txt"
echo "Artifacts in: $RUN_DIR" | tee -a "$RUN_DIR/commands.txt"
