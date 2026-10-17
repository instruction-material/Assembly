# ABI argument observations

Record role, compiler/version, build type, platform and commands. Preserve
predictions, the untouched observation and the single named repair separately.

| Current PC and instruction | RSP and owned slots | RDI RSI RDX RCX R8 R9 | RAX before/after | Next PC and reason |
| --- | --- | --- | --- | --- |

At lab_call predict the six argument registers. At lab_helper compare all six
actual values with that prediction and record its return-address word. For
the seven-argument investigation record the argument at helper-entry RSP+8,
distinguishing it from the return address and the padding slot.

Step through lab_helper_return to lab_after_call. Record which caller-saved
registers were cleared, the returned RAX and the reloaded original values.
At lab_return verify the original RSP and return address; step RET and record
the real caller PC. Do not infer these observations from the final value alone.

Retain the default and --changed runs, GCC/Clang Debug/Release checks, an
independently predicted unequal boundary pair and a rejected copied regression.
Explain why equal inputs conceal the named starter mistake. Preserve the
caller, C model, tests and ABI probe. Passing tests does not complete this trace.
