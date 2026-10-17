# Assembly

Source material for the Assembly course, centered on Linux x86-64 and the System V AMD64 ABI. Each project guide defines its target, tasks, build commands and completion contract.

## Native project sequence

| Course stage | Pack | Main purpose |
| --- | --- | --- |
| Setup | ASM-04-asm0-setup-and-tooling | Build and trace a mixed C/assembly function |
| Machine model | ASM-05-unit-1-machine-model-and-toolchain | Source/object/link/load evidence and bounded record loads |
| Registers | ASM1-Integer-Calculator | Signed arithmetic, division and bitwise operations |
| Arithmetic | ASM-06-unit-3-arithmetic-and-logic | Defined flags, implicit multiply/divide registers and deliberate fault traces |
| Loops | ASM2-Array-Sum-and-Search | Bounded walks and signed first-match search |
| Stack | ASM-07-unit-5-the-stack-and-function-calls | Nested calls, live values and balanced frames |
| ABI | ASM4-Call-C-Helper-from-Assembly | Real C-helper calls, arguments and alignment |
| Memory | ASM3-String-Length-and-Copy | Byte walks and bounded copying |
| Runtime | ASM5-Tiny-Command-Line-Parser | Signed operand parsing and command behavior |
| Compiler output | ASM-08-unit-9-reading-compiler-output | Working baseline plus actual compiler-output analysis |
| Debugging | ASM-09-unit-10-debugging-at-instruction-level | Deliberate branch fault, minimal repair and repeated trace |
| Performance | ASM-10-unit-11-performance-and-code-shape | Equivalent loops, actual timing and bounded interpretation |
| Hardening observation | ASM-25-unit-12-security-and-reliability-visibility-supplemental-2 | Real stack guards, PIE and runtime traces |
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

The root collection builds both role demos for all fourteen native packs above with Clang. Binaries are under build/bin/:

```sh
cmake -S . -B build
cmake --build build
```

This compiles the supplied programs; it does not imply that intentionally unfinished or faulty starters pass their completion contracts. Use each role's independent CMake build and project guide for the required tests and evidence.

The native CI workflow runs all fourteen project verifiers with Clang and GCC, including actual GDB checks, controlled regressions and the documented collection build. A verifier can also be run from this repository:

```sh
python3 test/verify_debug.py --cc clang --proof output/debug-clang.json
python3 test/verify_debug.py --cc gcc --proof output/debug-gcc.json
```

The performance verifier retains actual timing CSV, disassembly and monotonic-clock/debugger evidence; it does not enforce a speed winner. Run verify_performance.py with the same --cc/--proof arguments. The debugging verifier retains both the original faulty and corrected single-step traces. For the compiler project use verify_compiler.py and record actual generated listings; for the stack project use verify_stack.py and prove real calls/alignment. The other verifier filenames correspond to opening, calculator, array, string, helper, parser and reverse.

## Learning record

Read the target and function contract, predict a small example and follow the project's coding, observation or diagnosis task. Record instruction addresses, values before and after instructions, relevant flags and the evidence for each branch, call or return. Repeat the same trace after a correction, predict a changed case and keep the unchanged contracts passing. A guided session walks through the same evidence and reasoning used for independent study.

The Unit 3 arithmetic replacement has complete value/status contracts, independent Python-model checks and real divide-fault/GDB acceptance in its native verifier. Its current source review must pass both compiler jobs before the course selects an immutable site pin.

## Optional setup build investigations

The setup transfer pack investigates a local assembly definition that cannot
satisfy a separate C object's global reference. The separate extension pack
compares raw assembly input with assembly preprocessing and follows the resulting
macro relocation into the link diagnostic. Both include complete readings,
separate learner/reference roles and a build-evidence worksheet.

These optional investigations do not replace the required mixed-language setup
project. Each has its own CMake build; the collection build above remains the
fourteen-project sequence and does not build these intentionally failing starters.
Use the guide's fresh build directories before and after the single named repair.
Runtime tests do not complete the worksheet. The remaining 32 generic source
contexts remain under content audit.

Run the native acceptance with either compiler:

    python3 test/verify_setup_optional.py --cc clang --proof output/setup-optional-clang.json
    python3 test/verify_setup_optional.py --cc gcc --proof output/setup-optional-gcc.json

Each retains actual preprocessing, object symbols, relocations, disassembly,
failed and successful links, configured-value runs, CMake commands and process
lifecycles. Source-only checks never substitute for those native observations.

## Unit 8 owned syscall investigations

The former arithmetic-only transfer and extension folders now contain distinct
Linux x86-64 activities. One follows raw writes, libc error conversion, an
actual short write and full-pipe backpressure. The other follows the fourth
argument through openat and compares actual created modes and raw/libc errors.
Both retain complete readings, separate roles, strict contracts and trace sheets.
The existing parser and all fourteen earlier project verifiers remain intact.

Only the named routine.S task differs between learner and reference. The C
callers create and clean up their own pipes or temporary directories; the
contracts also check six preserved registers. The dedicated native compiler
jobs retain actual strace, debugger, object, build and process evidence:

    python3 test/verify_syscall_optional.py --cc clang --proof output/syscall-optional-clang.json
    python3 test/verify_syscall_optional.py --cc gcc --proof output/syscall-optional-gcc.json

A source-only run is a preparation check, not native acceptance. Each selected
role builds independently. These intentionally failing starters are separate
from the documented fourteen-project collection build.

## Register movement investigations

- [Partial-register writes](ASM-05-unit-2-registers-and-data-movement-supplemental-2/README.md) records actual AL, AX, EAX and RAX effects on complete output words.
- [Sign and zero extension](ASM-06-unit-2-registers-and-data-movement-supplemental-3/README.md) compares byte, word and doubleword interpretations with an explicit unsigned C model.

Each role includes its full caller, model, unchanged contracts, ABI probe, build definition and trace worksheet. The native register jobs retain both compilers' objects, source, independently checked result rows and actual single-step observations. Existing required calculator work stays separate.

## Optional comparison and shift investigations

Unit 3 adds signed/unsigned decision predicates and variable-count 64-bit shifts. Each standalone pack contains an unfinished named assembly operation, a separate correct reference, unchanged C17/ABI checks, an independent model and an observation worksheet. Build each selected role with its own CMake project; the required arithmetic project and collection build retain their contracts.

## Optional memory and effective-address investigations

Unit 1 adds a byte-order/access-width experiment over owned scratch bytes and a separate LEA base/index/scale/displacement experiment. Each selected role is a standalone C17/assembly CMake project with explicit checks and a trace worksheet. Complete the named learner operation before comparing with its separate reference. The required record-decoder project is preserved.

## Optional dispatch and loop investigations

Unit 4 adds selected-case fall-through and bounded-loop exit investigations. Their separate C17/assembly workspaces retain explicit boundary checks, native control-flow observations and trace worksheets. The required array-sum/search project is preserved.
