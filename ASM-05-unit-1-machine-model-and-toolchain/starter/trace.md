# Address and width trace

## Required source/object/link/load record

This worksheet continues the same core decoder attempt. Record the caller and
assembly object paths, ELF class/type/machine, the defined decoder symbol, the
caller's undefined reference, actual relocation offset/type, linked decoder
address, executable headers/interpreter, and the runtime address seen in GDB.
Explain what each stage supplies and what it has not established yet. Retain
the untouched starter's runtime failure beside its successful build and link.

Compare actual -O0 and -O2 compile commands and C caller disassembly in separate
build folders. Distinguish changes in the C caller from the handwritten decoder
instruction bytes. Keep the default and changed outputs for both builds. State
why whole-file hashes or addresses can change without a decoder .text change,
and why this comparison makes no timing or universal code-size claim.

| Stage/build | Artifact/command | Symbol or relocation | Actual observation | Meaning and limit |
| --- | --- | --- | --- | --- |
| Caller object | | | | |
| Decoder object | | | | |
| Linked executable | | | | |
| Runtime process | | | | |
| O0 versus O2 | | | | |

Predict each default record from the eight raw bytes before running it.
Record the Linux x86-64 environment, compiler, build directory and role.
Keep actual addresses from the current run; never copy a prior run's address.

| Record | Eight bytes | Predicted delta | Predicted size | Predicted tag | Actual result |
| --- | --- | --- | --- | --- | --- |
| 0 | | | | | |
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

Trace a completed decoder in GDB. Record the four argument registers, the
selected address calculation, bytes at that address, load instruction widths,
register contents after each load, output fields and return value. Explain LEA
versus memory access, little-endian byte order, sign versus zero extension,
and why a 32-bit destination write also clears the upper register half.

Repeat --changed, then trace a nonzero index. Explain which values changed and
which stride/offset rules did not. Retain the original starter failure and
the unchanged contracts after completing only routine.S. Name an error each
contract catches, a reason absolute addresses vary, and a limit of these
tests. The reference is a separate role. Passing code does not complete this
explanation; a guided walkthrough pauses at the same address/load boundaries.
