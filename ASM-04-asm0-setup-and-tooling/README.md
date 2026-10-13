# Opening Assembly project: build, call and trace a function

The required target is Linux x86-64 with the System V AMD64 ABI. Source uses
GNU/Clang preprocessed `.S` files and Intel syntax. Windows uses an x86-64 WSL2
Linux distribution. macOS uses an x86-64 Linux VM or lab. Native ARM64 and Mach-O
examples are separate comparisons; compiling with a host default is insufficient.

## Tools and layout

Check `uname -m` for `x86_64` and `uname -s` for `Linux`. On Ubuntu, install
`build-essential`, `clang`, `cmake`, `gdb` and `binutils` through its package
manager. Record compiler, CMake and debugger versions. The two role directories
are complete, separate projects. Work in `starter`; save it before opening the
separate `solution` reference. Keep experimental objects outside normal targets.

Each role contains `main.c`, `routine.S`, `transform.h`, `tests.c` and
`CMakeLists.txt`, plus an `abi_checks.S` contract helper. C supplies a checked caller and an independent expected-value
model. The named `ASM_TRANSFORM` task belongs in `routine.S`.

## Function contract and representation

`transform_value` accepts and returns a signed 32-bit value. Its result is the
low 32 bits of `2 * input + 5`, interpreted as a two's-complement signed value.
This is defined wrapping arithmetic in the assembly routine, not permission to
perform overflowing signed multiplication in C. The tests compute unsigned
32-bit arithmetic and copy its representation into `int32_t`.

Inputs 0, 1, -1, 3 and 19 produce 5, 7, 3, 11 and 43. The signed maximum produces
3; the signed minimum produces 5. Input -5 remains -5. Predict these results
before execution. Under this ABI the input occupies the low 32 bits of RDI
(EDI), and the result occupies EAX. Caller-saved registers may change; preserved
registers and the return stack state follow the ABI. An EAX write clears the
upper half of RAX. The C caller still interprets the returned low word as signed.

The default caller transforms 3, 7, 11 and 19 and sums the returned values in
`int64_t`. A completed run prints exactly `total=100` followed by a newline and
exits zero. The untouched identity implementation builds cleanly, but the
contract test fails and the demo emits an unfinished-task message to stderr
and exits 78. A successful build alone is incomplete evidence.

## Build and acceptance

From the selected role directory:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang
cmake --build build
ctest --test-dir build --output-on-failure
./build/assembly_demo
```

GCC uses `-DCMAKE_C_COMPILER=gcc` in a separate `build-gcc` directory. Repeat with
`-DCMAKE_BUILD_TYPE=Release` in another directory. The contract driver keeps its
checks active without `assert`, so Release cannot silently remove the gate.
Completed contracts check the preserved RBX, RBP and R12-R15 registers, then
cover twelve fixed patterns and 10,000 deterministic
patterns, including wrapping and signed boundaries. Keep build, test and demo
exit statuses separate. Direct compilation is also possible:

```sh
cc -std=c17 -Wall -Wextra -Wpedantic -Wconversion -Werror main.c routine.S -o demo
cc -std=c17 -Wall -Wextra -Wpedantic -Wconversion -Werror tests.c abi_checks.S routine.S -o contracts
./contracts
./demo
```

## Read and trace actual instructions

Use `objdump -d -M intel build/assembly_demo` to locate `transform_value`. The
reference computes its result with LEA and returns; the addressing notation
computes a value without dereferencing memory. Other implementations can use
separate arithmetic instructions. The contract does not require preserving
arithmetic flags or copying the reference instruction sequence.

In a Debug reference build:

```sh
gdb ./build/assembly_demo
```

Enter `set disassembly-flavor intel`, `break transform_value`, `run`, then
`info registers edi eax rip rsp` and `disassemble /r transform_value`. The first
startup check passes input zero, so predict EAX five. Use `stepi` until the
calculation finishes, inspect EAX, and step through the return. Before the
return, `x/gx $rsp` shows its saved return address. Addresses depend on the run;
record observed values instead of copying assumed addresses. `continue` lets
the caller finish. A multi-instruction implementation may need several steps.

Record the input word, result word, instruction address and return behavior.
Explain the difference between assembly arithmetic, C's expected-value model,
a compiler diagnostic, a failing contract and a successful demo. Independent
work and a guided walkthrough use these same predictions and recorded traces.

A deliberate offset change from five to six must make the contracts fail.
Restore the implementation and require the tests and demo to pass again.
The site editor's later import/export gate is a separate workflow check; this
native pack does not imply that the browser compiles or runs assembly.
