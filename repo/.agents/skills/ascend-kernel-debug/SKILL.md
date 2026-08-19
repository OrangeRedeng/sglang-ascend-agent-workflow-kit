---
name: ascend-kernel-debug
description: Diagnose crashing, incorrect, unsupported, or divergent Ascend/torch_npu/SGLang kernel behavior and route to the owning framework/kernel layer.
---
# Ascend kernel debug

1. Classify the operation before editing:
   - ordinary PyTorch op dispatched through torch_npu;
   - torch_npu-specific op/API;
   - sgl_kernel_npu custom kernel;
   - Triton-Ascend kernel;
   - AscendC/CANN custom op;
   - Python fallback.
2. If this is API/stream/memory/graph/format behavior, use `ascend-torch-npu` when installed rather than guessing framework semantics.
3. Minimize reproduction: shape, dtype, device, strides/layout/contiguity, graph/eager, hardware and exact versions.
4. Check in order: input contract -> dtype -> shape/alignment -> layout -> output contract -> alias/in-place -> async/streams -> synchronization -> graph capture -> kernel implementation.
5. For a custom op integration problem, use optional `ascend-opplugin`; for Triton/AscendC load only the corresponding kernel-development skill.
6. Use blocking/synchronization debug knobs only diagnostically; never leave them as a production fix.
7. Fix at the owning layer; do not hide a kernel bug with broad try/except or unconditional CPU fallback.
8. Validate the original failing configuration first.
