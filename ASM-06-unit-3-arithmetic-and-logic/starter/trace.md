# Arithmetic and flag evidence

This required record continues the same core arithmetic attempt. Preserve the
first predictions and untouched exit-78 result before inspecting the reference.

## Predictions and captured results

| Case/instruction | left/right bits | predicted value/auxiliary | defined mask | predicted CF/ZF/SF/OF | actual values | explanation |
| --- | --- | --- | --- | --- | --- | --- |
| MAX + 1 | | | | | | |
| UINT64_MAX + 1 | | | | | | |
| 0 - 1 | | | | | | |
| MIN - 1 | | | | | | |
| MIN * -1 | | | | | | |
| -21 / 4 | | | | | | |
| 21 / -4 | | | | | | |
| AND/OR/XOR | | | | | | |
| TEST/CMP | | | | | | |

Explain the result interpretation, unsigned carry/borrow versus signed
overflow, and why TEST/CMP preserve the stored left operand. State why only
CF/OF are reported for IMUL and no flag is claimed after IDIV. Undefined does
not mean cleared. Identify the actual producer whose flags were captured;
distinguish its flags from those of the dispatch or later mask instruction.

## Native instruction trace

Record Linux x86-64 target, ABI, compiler/binutils/GDB versions, role, build
directory and exact configure/compile commands. For ADD, record address,
instruction, RAX/R8 and masked flags before and after the real instruction.
For one-operand IMUL, retain both RDX and RAX and explain the full signed
product and its fit test. For IDIV, retain the sign-extended RDX:RAX pair,
divisor, quotient and remainder. Explain why clearing RDX differs from sign
extension for a negative dividend. Repeat --changed and explain the changed
carry/zero and remainder observations with current addresses.

## Rejection and deliberate fault

Retain unchanged public output for null/out-of-range operation and rejected
division cases. Separately record the owned probe PID, actual IDIV, input
registers and SIGFPE for zero and overflowing division in two child processes.
Contrast these faults with the public guards. Keep the normal passing contracts
and intentional fault evidence separate. No global signal/core policy changes
belong to this experiment.

## Compiler comparison and completion

Keep actual O0/O2 listings of arithmetic_c_mix, map its unsigned sum/AND/XOR
operations, and compare function-scoped observations with its checked output.
Retain compiler versions and flags; do not infer speed from source or listing
length. Include a changed full-width pair not copied from the example and
name one limit of the test set. Completion requires the two routine regions,
unchanged passing contracts and this explanation. Independent study and paced
discussion pause at the same flag producer, implicit operands and fault.
