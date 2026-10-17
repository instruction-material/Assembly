# Caller-Owned Locals Across a Nested Call

## Frame and return-address contract

The initial and incoming unsigned 64-bit values arrive in RDI and RSI, with an
owned output pointer in RDX. The routine subtracts 24 from RSP and stores initial,
incoming and the output pointer in offsets 0, 8 and 16 of its own frame.

With this function's scalar System V call, entry RSP is eight modulo sixteen.
Subtracting 24 makes it zero modulo sixteen before CALL. CALL pushes an
eight-byte return address, so `lab_helper` observes eight modulo sixteen.
If S is the outer entry RSP, the frame occupies S-24 through S-1, the nested
return address is at S-32, and the original return address remains at S.
The helper RET removes only the nested return address and resumes at
`lab_after_call` with RSP S-24.

The helper returns `initial XOR incoming` in RAX and its entry RSP modulo
sixteen in R10. It deliberately clears the caller-saved argument/scratch
registers RDI, RSI, RDX, R8 and R9. The caller then reloads its values and output
pointer from its owned frame. The fixed assembly helper makes that clobbering
visible; this investigation does not call a C helper.

## Predict and repair LOCAL_RELOAD

Five consecutive eight-byte outputs are the helper result, saved initial,
saved incoming, helper result plus initial modulo 2^64, and helper entry
alignment residue. For `initial=0102030405060708`,
`incoming=8000000000000005`:

| Field | Hexadecimal result |
| --- | --- |
| helper-result | 810203040506070d |
| saved-initial | 0102030405060708 |
| saved-incoming | 8000000000000005 |
| combined | 820406080a0c0e15 |
| helper-entry-alignment | 0000000000000008 |

The starter reloads initial from the incoming slot. Restore the named initial
reload to offset 0. Preserve the 24-byte allocation, nested call, helper and
remaining loads/stores. Releasing the frame must happen after all its local
slots have been read. The final RET must use the original caller return address.

At `lab_call`, record `p/x ((unsigned long)$rsp & 15)` and all three allocated
slots with `x/3gx $rsp`. Step CALL. Compare the helper's top word to
`p/x &lab_after_call`, record RSP and the return target, then step through
`lab_helper_return`. Observe the real return to `lab_after_call` before tracing
the local reloads. The final outputs must preserve the original inputs even
though the argument registers no longer contain them.

`--changed` uses `ffffffffffffffff` twice, giving helper result zero, both saved
values `ffffffffffffffff`, combined `ffffffffffffffff` and alignment eight.
Equal inputs conceal the starter's slot mistake. Predict an unequal pair
containing zero and one containing the high bit before testing either.

In a disposable reference copy, change only
`mov r9, QWORD PTR [rsp + 8] # saved incoming` to
`mov r9, QWORD PTR [rsp + 0] # wrong incoming slot`.
The unchanged contracts and default demonstration reject the incorrect saved
incoming field, while the equal-input changed demonstration still agrees.

This challenge focuses on frame lifetime and actual CALL/RET transitions. The
Unit 6 required C-helper project separately covers cross-language interoperability.

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
