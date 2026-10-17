# Switch Dispatch and Fall-Through Investigation

## Selected-case contract

The routine receives `initial` in RDI, a 64-bit payload in RSI and an owned
`LabResult *` output buffer in RDX. The normalized selector is `initial % 4`.
All arithmetic uses unsigned 64-bit wrapping. No payload value is used as a
memory address.

| Selector | Result | Visited-case mask | Comparisons |
| --- | --- | --- | --- |
| 0 | payload + 11 | 1 | 1 |
| 1 | payload XOR 0x55 | 2 | 2 |
| 2 | payload - 7 | 4 | 3 |
| 3 | payload | 8 | 3 |

Four consecutive eight-byte output slots contain the selector, result, visited
mask and comparison count. Bit `k` of the mask records execution of case `k`.
The count includes the tested comparisons even when they reject a case.

The dispatch chain compares ECX with 0, 1 and 2, then uses the default case.
Each `je` reads ZF from its immediately preceding compare. A selected case
computes its result and exits to `lab_join`; the final case reaches that join
by fall-through. MOV preserves the existing flags, but the program does not
rely on an older comparison surviving arbitrary case arithmetic.

## Predict and trace

The default pair is `initial=0000000000000001`,
`incoming=8000000000000005`. The expected fields are:

| Field | Hexadecimal value |
| --- | --- |
| selector | 0000000000000001 |
| result | 8000000000000050 |
| visited-case-mask | 0000000000000002 |
| comparisons | 0000000000000002 |

`--changed` uses selector 2 and payload `ffffffffffffffff`, producing result
`fffffffffffffff8`, visited mask 4 and comparison count 3. Predict selectors
0 and 3 with that payload as well, including the wrapped addition for case 0.

Record the actual path from `lab_check0` through the relevant compare labels,
the selected case and `lab_join`. Explain why a false equality branch reaches
the following instruction, while a true branch reaches its named target.
Keep the chosen-case prediction separate from the mask observed at the join.

## Named repair: DISPATCH_JOIN

The starter leaves the case-1 exit incomplete. Inspect the successor of its
`nop`: execution reaches case 2, overwrites the result and records both cases.
For the default input the observed result is `7ffffffffffffffe` and mask 6.
Restore the exit to the shared join without changing case arithmetic, the
dispatch comparisons or the output stores.

For a controlled regression, copy the reference and change only
`jmp lab_join # selected-case exit` to
`jmp lab_case0 # wrong selected-case exit`. Its default path now visits cases
1 and 0, resulting in `8000000000000010` and mask 3. The unchanged contracts
must reject it. The selector-2 changed demonstration still agrees, so that
single successful run cannot establish the selected-case contract.

This investigation concerns actual successors and case exits. The required
array-sum/search project remains the place to implement array traversal.

## Native workspace

The target is ordinary-user Linux x86-64, the System V AMD64 ABI and GNU Intel
assembly syntax. Use an x86-64 Linux lab or VM on macOS, or an x86-64 WSL
distribution on Windows. CMake 3.20+, GCC or Clang, GDB and binutils are required.
The site IDE edits, saves and exports source; compilation and instruction
stepping happen in that native environment.

Each selected role contains `routine.S`, `main.c`, `lab.h`, `model.c`, `tests.c`,
`abi_checks.S`, `CMakeLists.txt` and `trace.md`, with this shared README one
directory above it. The roles differ only in `routine.S`. Preserve the starter
attempt and its predictions when opening the separate reference.

From the extracted project folder, enter the selected `starter` or `solution`
directory and run:

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

Repeat with GCC in separate build directories by changing both compiler
arguments to `gcc`. Explicit comparisons keep the contracts active in Release.
An untouched starter builds, but its default demonstration exits 78 and the
contracts reject it. A completed starter and the separate reference pass.
An unsupported argument exits 64. A successful demonstration prints the input
pair followed by every result field as sixteen hexadecimal digits.

The C model computes expected results without calling the assembly routine.
The unchanged contract program tests every normalized count against sixteen
payload boundaries, then 10,013 deterministic additional pairs, for 10,269
cases. Its ABI wrapper also checks RBX, RBP, R12, R13, R14, R15 and stack
restoration. Keep those files unchanged; repair the named routine task and
record the observations in `trace.md`.

## Inspect the actual control flow

```sh
objdump -d -M intel --disassemble=lab_operation build-Debug/app
readelf -Ws build-Debug/CMakeFiles/app.dir/routine.S.o
gdb ./build-Debug/app
```

In GDB use `set disassembly-flavor intel`, `break lab_operation` and `run`.
Before each `si`, record `x/i $pc`, the relevant registers and the intended
successor address. After stepping a jump, inspect the new current PC. A label
names an address; merely reaching or passing its text in the source does not
perform a jump. Use `info registers rdi rsi rdx rax rcx r8 r9 eflags` and inspect
the owned output slots with `x/4gx $rdx` for dispatch or `x/5gx $rdx` for the loop
after `lab_join` has stored them. Stop at `lab_return` to observe the final
state before returning to the caller.

Retain the current disassembly addresses; they can change across compilers,
build types or repairs. The instruction following a compare is meaningful
only in relation to the flags that the compare actually produced. Instructions
inside a case or loop body may change flags, so use the next recorded compare
to explain the next conditional branch.

## Evidence to retain

- The predicted default/changed fields and the untouched observation.
- The minimal named repair, saved `routine.S` and completed `trace.md`.
- Actual current PCs before and after each relevant conditional or unconditional
  jump, with the register/flag evidence that explains its successor.
- GCC and Clang Debug/Release contract results and an independently chosen
  boundary pair with a prediction made before execution.
- The controlled regression in a disposable reference copy, its rejected
  default run/contracts and an explanation of any changed input that still
  happens to agree with the model.

Passing code does not complete the address trace or explain an observation.

Instruction reference: [Intel 64 and IA-32 instruction reference, Jcc and JMP](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=585).
