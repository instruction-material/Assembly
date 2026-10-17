# Memory observations

Record role, platform, compiler/version, build type and commands. Keep the
prediction, untouched observation and named repair separately.

| Current PC/instruction | Owned base and valid byte range | Actual address and width | Value before/after | Next PC and reason |
| --- | --- | --- | --- | --- |

For the pointer table draw four sixteen-byte records and four pointer slots.
Record the masked index, rotation, slot address, pointer stored in that slot,
selected record address and the field addresses. Separate address calculation
from the pointer load and the final field load. Use the pinned C offsets.

For the overlapping copy draw all sixteen original bytes and the source and
destination spans. Predict each byte read before its corresponding write.
Explain when a forward write destroys a later source byte. Record the actual
load/store PCs, offsets, remaining count and memory after each write.

Retain default/--changed observations, a separate boundary prediction, zero
length, both overlap directions, GCC/Clang Debug/Release checks and a rejected
copied regression. Preserve main.c, lab.h, model.c, tests.c and abi_checks.S.
Passing tests does not complete the address and memory trace.
