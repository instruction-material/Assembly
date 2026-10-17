# Effective Address Calculation Investigation

## Goal and starting point

After the required machine-model project, isolate base, index, scale and
displacement calculation. This optional extension uses LEA to produce numeric
64-bit results, so the arithmetic can be inspected independently of a memory
load. Predict each expression before running the learner and separate reference.

The 64-bit LEA instructions here calculate their effective-address expressions
and write RAX. They do not fetch data from the calculated numeric address and
leave arithmetic flags unchanged. The allowed encoded scales are 1, 2, 4 and 8.
A bracketed source in Intel syntax can therefore describe a calculation rather
than a memory read; the opcode determines the operation.

## Exact operation and learner task

RDI supplies `base=initial`; RSI supplies the index bit pattern `incoming`.
Every result is reduced modulo 2^64, matching the unsigned C model.

| Stage | Expression | Scale | Displacement |
| --- | --- | --- | --- |
| 0 | base + index | 1 | 0 |
| 1 | base + index * 2 | 2 | 0 |
| 2 | base + index * 4 + 13 | 4 | +13 |
| 3 | base + index * 8 − 7 | 8 | −7 |
| 4 | index * 8 | 8 | 0, no base |

Complete `ADDRESS_SCALE` at `lab_stage2`. The learner uses scale 2 where the
contract requires scale 4; preserve the base, displacement and output store.
With base `1000` and index `3` in hex, the incorrect row is `1013` rather than
`1019`. With the changed input, the index bit pattern represents −1 in two's
complement; unsigned wrapping defines the result without signed C overflow.

The generated values are integer bit patterns, not validated object pointers.
The function dereferences the actual owned RDX output buffer for its stores.
Keep the expressions as calculations rather than introducing a load through a
generated numeric address.

## Predicted reference results

Both command variants print `initial` and `incoming`, followed by these rows.

| Field | Default | --changed |
| --- | --- | --- |
| base-plus-index | `0000000000001003` | `ffffffffffffffef` |
| base-plus-index-times-2 | `0000000000001006` | `ffffffffffffffee` |
| base-plus-index-times-4-plus-13 | `0000000000001019` | `fffffffffffffff9` |
| base-plus-index-times-8-minus-7 | `0000000000001011` | `ffffffffffffffe1` |
| index-times-8 | `0000000000000018` | `fffffffffffffff8` |

Default input: initial `0000000000001000`, incoming `0000000000000003`.
Changed input: initial `fffffffffffffff0`, incoming `ffffffffffffffff`.

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

## Flags and copied regression

The routine executes `cmp rdi,rsi` once before the LEA stages. Record only the
defined CF/ZF/SF/OF bits from that producer before and after each LEA. The mask
`0x8c1` selects those four bits: default input predicts 0; the changed pair
predicts `0x81` (CF and SF). The output stores also preserve these flags. This
observation distinguishes the calculation from substituting flag-changing ADD
or shift instructions. Keep the current flags beside the actual opcode.

In a disposable correct-reference copy, change only stage 3's scale from 8 to 4.
Default output becomes `1005` rather than `1011`; the changed output becomes
`ffffffffffffffe5` rather than `ffffffffffffffe1`. Both demonstrations exit 78
and unchanged contracts reject that copy. Add zero index, all-ones index and
wrapping base/index combinations to the worksheet.

Primary architecture reference: [Intel Volume 2A, LEA](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf), including its 64-bit size rules and Flags Affected entry. The five expressions and input fixtures above are this lab's contract.
