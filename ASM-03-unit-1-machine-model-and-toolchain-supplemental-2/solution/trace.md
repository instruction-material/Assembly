# Memory and effective-address evidence

Record the Linux x86-64 target, selected role, compiler/version, build type and
commands. Keep the original prediction and untouched failure beside the repair.

| Stage | Current address / instruction | Input bytes or base/index/scale/displacement | RAX before | RAX after | Stored word | Explanation |
| --- | --- | --- | --- | --- | --- | --- |

For the memory investigation, draw all 16 owned bytes in increasing address
order, mark every load's byte span, and reconstruct each little-endian value.
Record the actual x/16bx $rsp dump at lab_stage0 before interpreting a load.
Explain why the offset-3 eight-byte span crosses the two original word values
while remaining entirely within the owned scratch area.

For the address investigation, expand each base/index/scale/displacement before
applying 64-bit wrapping. Record CMP-produced CF/ZF/SF/OF before and after LEA.
The generated bit patterns are integer results, not validated object pointers.
Explain how a calculation can finish without loading from that numeric address.

Retain the named minimal correction, default and --changed demonstrations,
GCC/Clang Debug/Release checks, one chosen boundary pair, and a rejected copied
regression. Keep the caller, unsigned-C model, tests and ABI wrapper unchanged.
Passing code does not fill the observation table or explain current addresses.
