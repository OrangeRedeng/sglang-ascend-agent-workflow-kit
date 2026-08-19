#!/usr/bin/env bash
set -u

printf '=== Git ===\n'
git rev-parse --short HEAD 2>/dev/null || true
git branch --show-current 2>/dev/null || true

printf '\n=== Python / PyTorch / torch_npu ===\n'
python3 - <<'PY_NPU_ENV'
import sys
print("python:", sys.version.split()[0])
try:
    import torch
    print("torch:", torch.__version__)
except Exception as e:
    print("torch: unavailable:", repr(e))
try:
    import torch_npu
    print("torch_npu:", getattr(torch_npu, "__version__", "unknown"))
except Exception as e:
    print("torch_npu: unavailable:", repr(e))
try:
    import torch
    print("npu_available:", torch.npu.is_available())
except Exception as e:
    print("npu_available: unavailable:", repr(e))
PY_NPU_ENV

printf '\n=== CANN paths / versions ===\n'
printf 'ASCEND_HOME_PATH=%s\n' "${ASCEND_HOME_PATH:-}"
printf 'ASCEND_OPP_PATH=%s\n' "${ASCEND_OPP_PATH:-}"
for f in \
  /usr/local/Ascend/ascend-toolkit/latest/version.cfg \
  /usr/local/Ascend/ascend-toolkit/latest/*version* \
  /usr/local/Ascend/latest/*version*
do
  [[ -f "$f" ]] && { echo "--- $f"; head -n 40 "$f"; }
done

printf '\n=== NPU ===\n'
if command -v npu-smi >/dev/null 2>&1; then
  npu-smi info || true
else
  echo "npu-smi not found (expected on a non-NPU local WSL workstation)."
fi

printf '\n=== Relevant environment ===\n'
env | grep -E '^(ASCEND|HCCL|GLOO|PYTORCH_NPU|STREAMS_PER_DEVICE|TASK_QUEUE_ENABLE|SGLANG_.*NPU)' | sort || true

printf '\n=== Installed NPU-related packages ===\n'
python3 -m pip list 2>/dev/null | grep -Ei 'torch|npu|cann|triton|sgl|deep.ep|deep_ep' || true
