# Comparison and shift evidence

Record the Linux x86-64 target, role, compiler/version, build type and commands.
Preserve the first prediction and untouched failure before opening a reference.

| Stage | Current address / instruction | Inputs and interpretation | RAX before | RAX after | Stored word | Explanation |
| --- | --- | --- | --- | --- | --- | --- |

For comparisons, record the CMP-produced CF/ZF/SF/OF at each SETcc and the
signed/unsigned truth value. Explain why MOV EAX,0 retains that producer while
XOR EAX,EAX does not. For shifts, record CL and its effective six-bit count,
the three resulting bit patterns, and the count slot. This result contract
does not report shift flags; undefined observations are not portable rules.

Retain the named minimal correction, default and --changed demonstrations,
GCC/Clang Debug/Release checks, a chosen boundary pair, and one rejected copied
regression. Keep the caller, unsigned-C model, tests and ABI wrapper unchanged.
Passing code does not fill this table or explain the current instructions.
