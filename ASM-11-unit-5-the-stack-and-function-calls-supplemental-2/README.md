# LIFO Value Order and Stack Restoration

## Contract and stack layout

`lab_operation(initial, incoming, output)` receives the two unsigned 64-bit
values in RDI and RSI and an owned output pointer in RDX. Four consecutive
eight-byte outputs are: first popped value `incoming`, second popped value
`initial`, `initial - incoming` modulo 2^64, and restored-stack delta zero.
The output pointer is never derived from an input value.

Let S be RSP at function entry. `[S]` contains the caller's return address.
`push rdi` allocates `[S-8]` and stores initial; `push rsi` then allocates
`[S-16]` and stores incoming. POP reads the current top word before advancing
RSP by eight. The first POP therefore receives incoming and the second initial.
The two POPs leave the original return address at [S]. This routine makes
no nested call and restores RSP before its final RET.

## Predict and repair LIFO_POP

For `initial=0102030405060708`, `incoming=8000000000000005`, predict:

| Field | Hexadecimal result |
| --- | --- |
| first-pop | 8000000000000005 |
| second-pop | 0102030405060708 |
| initial-minus-incoming | 8102030405060703 |
| stack-delta | 0000000000000000 |

The untouched starter uses the opposite register destinations for the two POPs.
It balances the stack but swaps the output roles and reverses the subtraction.
Repair those destinations while preserving the pushes, arithmetic and stores.
At `lab_pops` predict both owned words; at `lab_restored` check RAX, RCX and RSP.
Explain the distinction between last-in/first-out order and the subtraction's
operand order.

`--changed` supplies `ffffffffffffffff` for both values. Both pops then look
identical and the difference is zero, even in the untouched starter. This
successful special case does not establish the contract. Predict unequal
pairs `(0, ffffffffffffffff)` and `(ffffffffffffffff, 0)` before running them.

For a controlled regression in a reference copy, change only
`push rdi # save initial first` to `push rsi # wrong first saved value`.
The routine still balances its stack, but saves incoming twice. The default
run and unchanged contracts must reject it; the equal-input changed run agrees.
Keep the regression separate from the repaired starter.

This optional investigation isolates stack value order. The required Unit 5
project provides the broader function-frame work.

## Native workspace

Use ordinary-user Linux x86-64, the System V AMD64 ABI and GNU Intel assembly
syntax. On macOS use an x86-64 Linux lab or VM; on Windows use an x86-64 WSL
distribution. CMake 3.20+, GCC or Clang, GDB and binutils are required. The site
IDE edits, saves and exports these files; native compilation and instruction
stepping use that Linux environment.

Each role contains `routine.S`, `main.c`, `lab.h`, `model.c`, `tests.c`,
`abi_checks.S`, `CMakeLists.txt` and `trace.md`. The roles differ only in
`routine.S`. Keep the starter attempt and predictions when inspecting the
separate reference. The shared README belongs one level above the selected
role folder.

From the selected `starter` or `solution` directory:

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
```

Repeat with both compiler arguments set to `gcc` in separate build directories.
The untouched starter compiles, but its default demonstration exits 78 and
the contracts fail. Repair only the named task in `routine.S`. The completed
starter and separate reference pass. Unsupported arguments exit 64. Successful
runs print both inputs and every output field as sixteen hexadecimal digits.

The unchanged C model computes expected values without calling the assembly
routine. The contracts cover sixteen boundary values crossed with themselves
and 10,013 deterministic additional pairs, for 10,269 cases. Explicit checks
remain active in Release. The ABI probe also checks RBX, RBP, R12, R13, R14,
R15 and stack restoration. Preserve `main.c`, `lab.h`, `model.c`, `tests.c` and
`abi_checks.S`; complete the observation table in `trace.md` separately.

## Observe current addresses

```sh
objdump -d -M intel build-Debug/app
readelf -Ws build-Debug/CMakeFiles/app.dir/routine.S.o
gdb ./build-Debug/app
```

In GDB use `set disassembly-flavor intel`, `break lab_operation` and `run`.
At entry save `set $entry_sp = $rsp`,
`set $return_pc = *(unsigned long long*)$rsp` and `set $output = $rdx`.
Before each `si`, record `x/i $pc`, `info registers rsp rax rcx rdi rsi rdx r8 r9 r10 r11`
and `x/gx $rsp`. Read only valid local slots or the return-address word that
the current instruction has established. Addresses can differ across builds;
derive them from the current run.

At `lab_return`, verify `$rsp == $entry_sp` and the top word still equals
`$return_pc`. Inspect the output through the saved `$output` pointer. Step RET
and verify `$pc == $return_pc` and `$rsp == $entry_sp + 8`. A balanced stack
alone does not prove correct output values.

## Evidence to retain

- Default and changed predictions, untouched observations and minimal repair.
- The actual instruction PCs, stack slots and return-address transitions in
  `trace.md`, including the final return to the caller.
- GCC and Clang Debug/Release contract results and an independently predicted
  unequal boundary pair.
- A disposable controlled regression, its rejected default/contracts and an
  explanation of why equal inputs conceal it.

Instruction semantics: [Intel software developer manuals, PUSH/POP/CALL/RET](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html).
Stack and register contract: [System V AMD64 ABI, function calling sequence](https://gitlab.com/x86-psABIs/x86-64-ABI/-/blob/master/x86-64-ABI/low-level-sys-info.tex).
