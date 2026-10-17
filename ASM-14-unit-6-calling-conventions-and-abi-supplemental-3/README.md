# Seventh Integer Argument and Stack Location

## Argument and result contract

The outer `lab_operation(uint64_t initial, uint64_t incoming, LabResult *output)`
receives its inputs in RDI and RSI and its owned output pointer in RDX. It calls
the fixed assembly helper once with these unsigned 64-bit scalar arguments:

| Argument | Value | Location at helper entry |
| --- | --- | --- |
| 1 | initial | RDI |
| 2 | incoming | RSI |
| 3 | initial XOR incoming | RDX |
| 4 | initial + incoming | RCX |
| 5 | bitwise complement of initial | R8 |
| 6 | bitwise complement of incoming | R9 |
| 7 | initial - incoming | eight bytes above helper-entry RSP |

All arithmetic uses unsigned 64-bit wrapping. The helper returns the weighted
sum `a1 + 3*a2 + 5*a3 + 7*a4 + 11*a5 + 13*a6 + 17*a7`
in RAX. Three consecutive output words are that result, original initial and
original incoming. No scalar value is used as a memory address.

The helper deliberately clears caller-saved argument/scratch registers after
computing its return value. The outer routine reloads its output pointer and
original inputs from its own frame. RBX, RBP and R12 through R15 must retain
their entry values. The reference follows the System V AMD64 scalar convention;
the helper is assembly so every argument and clobber can be single-stepped.
The required Unit 6 project separately supplies a real C-helper interface.

## Predict and repair STACK_ARGUMENT

The default values are `initial=0102030405060708` and
`incoming=8000000000000005`. Compute all argument values before the call.
The correct helper result is `9326394c5f728535`.
The other output words preserve those two original inputs.

The starter stores the seventh argument in the padding slot at outer RSP+32.
The actual argument slot at outer RSP remains zero. Repair only the displacement
of the named store, moving it to outer RSP+0. Preserve the argument value,
40-byte allocation, helper and all other saved slots.

If S is entry RSP, the caller allocates 40 bytes: seventh argument at S-40,
output pointer at S-32, initial at S-24, incoming at S-16 and padding at S-8.
RSP is zero modulo sixteen before CALL. CALL pushes its return address at S-48.
The helper therefore reads argument seven from helper RSP+8, which is S-40.
The return address is at helper RSP+0. Padding is not an argument slot. The
helper RET resumes at lab_after_call with RSP S-40. Restore the frame after
reloading its original values and pointer.

In a disposable reference copy change `imul r11, r11, 17` to
`imul r11, r11, 19`. The location is still valid but the seventh argument's
contribution violates its contract. The default and unchanged checks reject it.

`--changed` uses `ffffffffffffffff` twice. Equal inputs conceal the starter's
mistake and the copied regression; a passing special case is insufficient.
Predict an unequal zero/high-bit pair before testing it. The untouched starter
builds, but the default demonstration exits 78 and its contracts fail. Complete
only STACK_ARGUMENT in `routine.S`; the repaired starter and separate reference pass.

## Native workspace and checks

Use ordinary-user Linux x86-64, GNU Intel assembly syntax, CMake 3.20+, GCC or
Clang, GDB and binutils. On macOS use an x86-64 Linux lab or VM; on Windows
use an x86-64 WSL distribution. The site IDE edits, saves and exports the files;
builds and instruction stepping use this native Linux environment.

Each role has `routine.S`, `main.c`, `lab.h`, `model.c`, `tests.c`, `abi_checks.S`,
`CMakeLists.txt` and `trace.md`. Roles differ only in the assembly routine.
Keep `README.md` one level above the selected role. From that role directory:

```sh
cmake -S . -B build-Debug -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-Debug --verbose --parallel 1
./build-Debug/app
ctest --test-dir build-Debug --output-on-failure
./build-Debug/app --changed
cmake -S . -B build-Release -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-Release --verbose --parallel 1
ctest --test-dir build-Release --output-on-failure
./build-Release/app --changed
objdump -d -M intel build-Debug/app
gdb ./build-Debug/app
```

Repeat with both compiler arguments set to `gcc` in separate build directories.
Unsupported arguments exit 64. The C model uses unsigned arithmetic without
calling the assembly helper. Unchanged checks cover sixteen boundary values
crossed with themselves and 10,013 additional deterministic pairs, for 10,269
cases; explicit checks remain active in Release. The ABI probe checks the six
preserved registers and restored stack. Numeric agreement alone does not prove
the observed call mapping; complete `trace.md` separately.

## Observe the actual call

In GDB use `set disassembly-flavor intel`, `break lab_operation` and `run`.
Save `set $entry_sp = $rsp`, `set $return_pc = *(unsigned long long*)$rsp`
and `set $output = $rdx`. At lab_call record all six argument registers and
`p/x ((unsigned long)$rsp & 15)`. Step CALL, record its pushed return address
and the helper's argument state, then step through lab_helper_return. Record
RAX and the cleared argument registers at lab_after_call before the reloads.
At lab_return verify the original RSP and return address, inspect outputs via
`$output`, then step RET to verify `$pc == $return_pc` and
`$rsp == $entry_sp + 8`. Use current addresses from this run.

Retain predictions, untouched behavior, the named repair, complete actual call
trace, both compiler/build contracts, a boundary prediction and the rejected
copied regression. Preserve main.c, lab.h, model.c, tests.c and abi_checks.S.

Calling sequence reference: [System V AMD64 ABI](https://gitlab.com/x86-psABIs/x86-64-ABI/-/blob/master/x86-64-ABI/low-level-sys-info.tex).
