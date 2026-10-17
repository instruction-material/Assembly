# Loop Exit Boundary and Invariant Investigation

## Bounded-loop contract

The routine receives `initial` in RDI, a 64-bit payload in RSI and an owned
`LabResult *` output buffer in RDX. Normalize the count as `initial % 16`, so
the correct routine executes zero through fifteen body visits. Values and
accumulation use unsigned 64-bit wrapping.

| Output slot | Meaning | Expected value for normalized count n |
| --- | --- | --- |
| 0 | count | n |
| 1 | sum | n times payload, modulo 2^64 |
| 2 | body-visits | n |
| 3 | visited-index-mask | 2^n - 1 |
| 4 | exit-index | n |

At `lab_check`, RDI holds n, RCX holds the next index, RAX holds the sum, R9
counts completed body visits and R8 records visited indices. Initially the
index, sum, visits and mask are zero. Before the correct loop's check at index
k, its invariant is `0 <= k <= n`, sum is `k * payload` modulo 2^64, visits are
k and the mask is `2^k - 1`.

`cmp rcx, rdi` compares the index with the count. The unsigned `jae` exits
when the index is at least the count, including equality. `ja` excludes the
equality case. At equality CF is zero and ZF is one, so the two conditions
choose different successors. Each completed body sets bit k, adds one payload
and increments both counters before returning to the check. Since n is at
most fifteen, each visited bit is within the 64-bit mask.

## Predict and trace

The default pair is `initial=0000000000000003`,
`incoming=8000000000000005`. The correct fields are:

| Field | Hexadecimal value |
| --- | --- |
| count | 0000000000000003 |
| sum | 800000000000000f |
| body-visits | 0000000000000003 |
| visited-index-mask | 0000000000000007 |
| exit-index | 0000000000000003 |

`--changed` uses count zero and payload `ffffffffffffffff`; every output is
zero and the body is never entered. Also predict count one and count fifteen
with that payload. The sums are respectively `ffffffffffffffff` and
`fffffffffffffff1`; the masks are 1 and `7fff`.

Trace every default check and its chosen successor. At index 3 record the
immediately preceding comparison and explain the exit using CF and ZF. For
the zero-count case, record the first comparison and the direct path to the
join. The exit index and body-visit count are separate observations even when
the correct routine makes them equal.

## Named repair: LOOP_EXIT

The starter exits only when the index is above the count. It executes the
equality iteration as well, including one visit for a zero count. On the
default input it produces sum `0000000000000014`, four visits, mask `f` and
exit index 4 while the normalized count remains 3. Correct the unsigned exit
condition so the equality state reaches the join before entering the body.
Preserve the compare, body, normalization and output stores.

For a controlled regression in a reference copy, change only
`add rax, rsi` to `sub rax, rsi`. The default sum becomes
`7ffffffffffffff1`; the body-count and mask fields still look correct. The
unchanged contracts must reject the accumulator error. The zero-count
changed demonstration still agrees because neither version enters the body.

This challenge adds an explicit invariant and exit-boundary proof. It retains
the required array-sum/search project and its separate traversal requirements.

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
