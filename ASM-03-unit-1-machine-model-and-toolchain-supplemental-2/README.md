# Byte Order and Memory Access Width Investigation

## Goal and starting point

After the required record-decoder project, isolate how a memory byte span becomes
a register value. This optional investigation keeps addresses, access widths and
numeric interpretation visible one operation at a time. Predict the complete
table before running the untouched learner or opening the separate reference.

On this x86-64 target, a stored integer places its least significant byte at the
lowest address. The numerical hex notation displays the most significant digit
first; a memory dump lists bytes by address. Reading those two displays in the
same direction produces a false byte-order conclusion. Each load's width is a
separate question from the width of the value printed afterward.

The routine reserves 24 stack bytes, stores `initial` at offsets 0–7 and
`incoming` at offsets 8–15, then reads only that initialized 16-byte region.
It restores the reservation before returning. For the default input, the bytes
at increasing addresses from the current RSP are:

~~~text
offset: 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
byte:   08 07 06 05 04 03 02 01 88 97 a6 b5 c4 d3 e2 f1
~~~

## Exact operation and learner task

| Stage | First byte offset | Bytes read | Meaning |
| --- | --- | --- | --- |
| 0 | 0 | 1 | Zero-extended byte |
| 1 | 1 | 2 | Zero-extended word |
| 2 | 4 | 4 | Dword loaded through EAX |
| 3 | 0 | 8 | Full first word value |
| 4 | 3 | 8 | Span across the two stored word values |
| 5 | 8 | 8 | Full second word value |

Complete `MEMORY_SPAN` at `lab_stage4`. The learner currently reads four bytes
through EAX, losing the upper bytes of the documented eight-byte span. Use the
full QWORD load into RAX at the same offset and preserve the following store.
The offset-3 span covers bytes 3–10, entirely within the initialized area.
This ordinary x86-64 load can be unaligned; the portable C model reconstructs
bytes explicitly rather than casting an unaligned C pointer.

For bytes b0 through b(n−1), the model value is the sum of
`b[i] * 256^i`. All intermediate values are unsigned and the largest shift is
56 bits. Reconstruct the offset-3 default value from its eight individual bytes;
reading only the first four instead produces `0000000002030405`.

## Predicted reference results

Both command variants print `initial` and `incoming`, followed by these rows.

| Field | Default | --changed |
| --- | --- | --- |
| byte-at-0 | `0000000000000008` | `00000000000000ff` |
| word-at-1 | `0000000000000607` | `0000000000000000` |
| dword-at-4 | `0000000001020304` | `0000000080000000` |
| qword-at-0 | `0102030405060708` | `80000000000000ff` |
| cross-qword-at-3 | `a697880102030405` | `0000018000000000` |
| qword-at-8 | `f1e2d3c4b5a69788` | `0000000000000001` |

Default input: initial `0102030405060708`, incoming `f1e2d3c4b5a69788`.
Changed input: initial `80000000000000ff`, incoming `0000000000000001`.

## Native target and files

Use an ordinary-user Linux x86-64 VM or lab, the System V AMD64 ABI, GNU Intel
assembly syntax, C17, CMake 3.20+, Clang and GCC, GDB, and binutils. A macOS or
Windows editor can save the source; run these native commands in the Linux lab.

Select `starter` or the separate `solution` directory. Its eight files are
`routine.S`, `main.c`, `lab.h`, `model.c`, `tests.c`, `abi_checks.S`,
`CMakeLists.txt`, and `trace.md`. Keep this shared README beside that directory.
The required record-decoder project remains a separate saved attempt.

The function takes the initial 64-bit bits in RDI, incoming 64-bit bits in RSI,
and a valid, owned `LabResult` output buffer in RDX. Each output field occupies
eight bytes. Preserve RBX, RBP, R12–R15 and restore the original stack pointer.
The unchanged ABI probe checks those obligations and the output guard words.

## Build and retain the first result

From the selected role directory:

~~~sh
cmake -S . -B build-Debug -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build-Debug --verbose --parallel 1
./build-Debug/app
ctest --test-dir build-Debug --output-on-failure
./build-Debug/app --changed
~~~

The untouched learner builds, but the demonstrations exit 78 and print no
successful result rows; the unchanged contracts fail. Keep that first diagnostic
and its prediction. After the named one-instruction repair, both demonstrations
exit 0 and the contracts report 10269 independent machine-model cases.
Unrecognized command arguments exit 64.

~~~sh
cmake -S . -B build-Release -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build-Release --verbose --parallel 1
ctest --test-dir build-Release --output-on-failure
./build-Release/app --changed
cmake -S . -B build-gcc-Debug -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=gcc -DCMAKE_ASM_COMPILER=gcc -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build-gcc-Debug --verbose --parallel 1
ctest --test-dir build-gcc-Debug --output-on-failure
./build-gcc-Debug/app --changed
~~~

Repeat the GCC configuration with a separate Release directory. Explicit value,
guard and ABI comparisons remain active with NDEBUG. Preserve compiler/version,
actual flags from `compile_commands.json`, output and exit status for each run.
The C model is separate from the assembly; the native acceptance oracle uses
another deterministic input stream and mathematical implementation.

## Observe the actual instructions

~~~sh
objdump -d -M intel --disassemble=lab_operation build-Debug/app
readelf -Ws build-Debug/CMakeFiles/app.dir/routine.S.o
gdb ./build-Debug/app
~~~

In GDB, use `set disassembly-flavor intel`, `break lab_stage0`, and `run`.
Add the later stage breakpoints. At each, retain `x/i $pc`,
`info registers rdi rsi rdx rax rsp rip eflags`, and the RAX value before and
after `si`. Step the following store and inspect its actual output slot with
`x/gx $rdx` at stage 0, then `$rdx+8`, `$rdx+16`, and the later eight-byte offsets.
Use the current addresses and disassembly rather than copying reference addresses.
Each operation and its store are adjacent to the next stage. After stepping the
store, the current PC is already at that next label: observe it directly rather
than continuing past its breakpoint. Compare the PC with the named stage address.

## Completion evidence

Complete only the named instruction in `routine.S` and the observation worksheet
in `trace.md`; retain the caller, header, C model, tests and ABI probe unchanged.
Keep predicted and observed default/changed rows, the original failure, the
minimal correction, all compiler/build profiles, one additional boundary pair,
and the controlled copied regression beside its rejected contract result.
The separate reference supplies correct code, while the worksheet still requires
actual instruction addresses and register or memory observations. Passing tests
does not complete that explanation. The same predictions and checkpoints support
a shared walkthrough without changing the required evidence.

## Byte dump and copied regression

At `lab_stage0`, use `x/16bx $rsp`. Match all 16 actual bytes to the two input
words before stepping a load. Record both the input-memory address and the
separate output-slot address. Mark byte spans 1–2 and 3–10 explicitly.
The changed data checks a high input bit, zero middle bytes, a low FF byte,
and a nonzero cross-word contribution. Add zero, all-ones and a chosen single-bit
input pair to the worksheet.

In a disposable copy of the correct reference, insert `bswap rax` immediately
after the stage-3 QWORD load and before its output store. The native load already
formed the intended integer, so this reversal changes the stage-3 result. Both
documented demonstrations then exit 78 and unchanged contracts reject the copy.
Retain that observation separately from the completed learner.

Primary architecture reference: [Intel Volume 1, Bit and Byte Order](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-1-manual.pdf), section 1.3.1. The tables above describe this lab's explicit owned byte layout.
