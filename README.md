# Assembly

Source material for the Assembly course, centered on Linux x86-64 and the System V AMD64 ABI. Each project guide defines its target, tasks, build commands and completion contract.

## Native project sequence

| Course stage | Pack | Main purpose |
| --- | --- | --- |
| Setup | ASM-04-asm0-setup-and-tooling | Build and trace a mixed C/assembly function |
| Registers | ASM1-Integer-Calculator | Signed arithmetic, division and bitwise operations |
| Loops | ASM2-Array-Sum-and-Search | Bounded walks and signed first-match search |
| Stack | ASM-07-unit-5-the-stack-and-function-calls | Nested calls, live values and balanced frames |
| ABI | ASM4-Call-C-Helper-from-Assembly | Real C-helper calls, arguments and alignment |
| Memory | ASM3-String-Length-and-Copy | Byte walks and bounded copying |
| Runtime | ASM5-Tiny-Command-Line-Parser | Signed operand parsing and command behavior |
| Compiler output | ASM-08-unit-9-reading-compiler-output | Working baseline plus actual compiler-output analysis |
| Debugging | ASM-09-unit-10-debugging-at-instruction-level | Deliberate branch fault, minimal repair and repeated trace |
| Performance | ASM-10-unit-11-performance-and-code-shape | Equivalent loops, actual timing and bounded interpretation |
| Reverse engineering | ASM6-Reverse-Engineering-Toy-Program | Recover a course-owned routine's behavior |

Each pack has an independent learner starter/, reference solution/ and shared README.md. Select the learner role first and use the site course's learning path for the additional unit and studio assignments.

## Native setup and completion

Use Linux x86-64, CMake 3.20 or later, Clang or GCC, GDB and objdump. On macOS use an x86-64 Linux VM/lab; on Windows use an x86-64 WSL distribution. From a selected project folder:

```sh
cmake -S starter -B build-starter -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-starter
ctest --test-dir build-starter --output-on-failure
```

The project guide explains how to interpret those results. In a coding project, an unfinished starter fails the unchanged contracts until its named task is completed. The compiler-output and performance projects instead supplies working role programs; complete analysis.md with actual observations. The debugging project compiles but reproduces a known signed-branch error; retain the failing trace before making the minimal repair. Successful code tests alone do not complete an analysis worksheet.

Use separate folders for reference, GCC and Release builds. Preserve learner work before consulting the reference. Follow the compiler-output guide's explicit -O0/-O2 flags when comparing that project.

## Collection build and verification

The root collection builds both role demos for all eleven native packs above with Clang. Binaries are under build/bin/:

```sh
cmake -S . -B build
cmake --build build
```

This compiles the supplied programs; it does not imply that intentionally unfinished or faulty starters pass their completion contracts. Use each role's independent CMake build and project guide for the required tests and evidence.

The native CI workflow runs all eleven project verifiers with Clang and GCC, including actual GDB checks, controlled regressions and the documented collection build. A verifier can also be run from this repository:

```sh
python3 test/verify_debug.py --cc clang --proof output/debug-clang.json
python3 test/verify_debug.py --cc gcc --proof output/debug-gcc.json
```

The performance verifier retains actual timing CSV, disassembly and monotonic-clock/debugger evidence; it does not enforce a speed winner. Run verify_performance.py with the same --cc/--proof arguments. The debugging verifier retains both the original faulty and corrected single-step traces. For the compiler project use verify_compiler.py and record actual generated listings; for the stack project use verify_stack.py and prove real calls/alignment. The other verifier filenames correspond to opening, calculator, array, string, helper, parser and reverse.

## Learning record

Read the target and function contract, predict a small example and follow the project's coding, observation or diagnosis task. Record instruction addresses, values before and after instructions, relevant flags and the evidence for each branch, call or return. Repeat the same trace after a correction, predict a changed case and keep the unchanged contracts passing. A guided session walks through the same evidence and reasoning used for independent study.
