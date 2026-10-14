# Unit 10: Debugging at Instruction Level

Revisit the earlier array-search idea with a deliberately faulty branch.
The required work is diagnosis, a minimal repair and a before/after trace,
not another implementation of the earlier search project. The starter
compiles successfully but returns a wrong signed index. Preserve the
failing evidence before editing routine.S, and complete analysis.md.

## Target, files and contract

Use Linux x86-64, the System V AMD64 ABI, GNU/Clang Intel assembly, C17,
CMake 3.20+, Clang or GCC, GDB and objdump. Use an x86-64 Linux VM/lab on
macOS or an x86-64 WSL distribution on Windows. Record the actual target,
compiler version and flags; debugger addresses vary between builds.

Each independent role has routine.S, debug_lab.h, main.c, tests.c,
abi_checks.S, CMakeLists.txt and analysis.md. The routine returns the first
index whose int32_t value is signed >=0, or -1 when none exists. Its inputs
are the array pointer in RDI and signed int64_t count in RSI; return in RAX.
For count<=0, values may be null and must not be accessed. Positive counts
require count readable entries. Do not write input, read past count, damage
the caller frame or change RBX, RBP and R12 through R15.

## Reproduce before repairing

From the project folder:

```sh
cmake -S starter -B build-starter -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-starter
./build-starter/assembly_debug
ctest --test-dir build-starter --output-on-failure
```

For {-8,-1,4}, predict index 2. The untouched demo prints observed=0 expected=2,
reports the known comparison bug on stderr and exits 1. CTest fails for the
same semantic error. This expected failure is the evidence to investigate;
do not change the expected test answer or replace the routine wholesale.

## Stop at the first wrong instruction decision

```sh
gdb ./build-starter/assembly_debug
```

At the GDB prompt:

```text
set disassembly-flavor intel
tbreak *debug_branch_decision
run
info registers rcx r8 eflags rip rsp
print (int)$r8
x/3dw $rdi
x/i $pc
si
x/i $pc
finish
print $rax
continue
```

The breakpoint is immediately after CMP R8D,0 and before the conditional
branch. Record the instruction address, the value before the instruction,
the value after the instruction and the evidence for the next branch, call,
or return. Initially RCX=0 and R8D=0xfffffff8, signed -8. The comparison gives
SF=1, OF=0, ZF=0 and CF=0. JAE tests the unsigned carry condition CF=0, so the
faulty decision jumps to debug_found and returns 0. The bytes and comparison
are correct; the wrong interpretation of flags is the first bad transition.

## Minimal correction and identical trace

After saving that evidence, correct DEBUG_SIGNED_BRANCH in starter/routine.S
using the signed >= condition. JGE tests SF==OF: it skips -8 and -1, accepts
4 and returns index 2. Rebuild, rerun the same breakpoint and single step,
and compare the actual next instruction and return. Both the demo and CTest
must pass after the correction. Keep the memory/count guards intact.

## Changed case, build modes and complete evidence

Predict {-8,0,4} before editing the demo array and its expected index together.
The correct index is 1; a strict greater-than branch incorrectly skips zero.
Save this case and explanation in analysis.md. The contracts exercise 10,015
fixed/deterministic and negative-count cases plus four physical readonly/
guard-page cases per profile, with six preserved-register checks. Passing
code tests alone does not complete the worksheet.

For the reference, replace starter with solution and use a different build
folder. Repeat with both compiler settings changed to gcc. Compare Debug
and Release in separate folders. The collection build includes both roles;
building its faulty starter is valid, while executing it still exposes the
known bug until repaired.

Independent study follows prediction, failure capture, one-instruction
diagnosis, minimal correction, repeated trace and changed-case proof. A
guided session uses the same record to discuss each transition before
editing. The optional extension can inspect the same decision without
source-line stepping, using objdump -d -M intel and actual symbol addresses.

## References

- [GDB registers and next-instruction inspection](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Registers.html)
- [GDB instruction stepping and function return](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)
