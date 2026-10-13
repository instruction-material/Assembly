# Integer calculator: 64-bit operands and checked dispatch

The required target is Linux x86-64, the System V AMD64 ABI, GNU/Clang
preprocessed `.S` source and Intel syntax. Use an x86-64 Linux lab or VM on
macOS, or an x86-64 WSL distribution on Windows. Native ARM64 and Mach-O
comparisons are separate work. Confirm `uname -s` is `Linux` and `uname -m`
is `x86_64`. The lab needs a C compiler, assembler, CMake, GDB and binutils.

## Project purpose and files

Trace a pair of 64-bit operands and a one-byte operator through register-based
dispatch. Predict each selected branch and returned value before execution.
Then use the native tests and a debugger to check the prediction. Independent
work and an instructor walkthrough use the same examples and trace evidence.

Each selected role is a complete project: `main.c`, `calculator.S`,
`calculator.h`, `tests.c`, `abi_checks.S` and `CMakeLists.txt`. The C caller
validates input, checks implementation readiness, and prints results. Assembly
computes the expression. The contract driver supplies an independent C model;
the ABI helper checks RBX, RBP and R12-R15 preservation for every operator.

Addition, subtraction and multiplication already work in the starter. Preserve
those implementations. Complete only `CALC_DIV`, `CALC_AND` and `CALC_XOR` in
`calculator.S` to add signed division, bitwise AND and bitwise XOR. The starter
builds but fails its contracts. Its demo prints an unfinished-task message to
stderr and exits 78 without successful result rows. A build alone does not
show that the three missing operator paths work.

## Exact arithmetic contract

The function is `int64_t asm_eval_expression(int64_t left, int64_t right,
char op)`. Valid operators are `+`, `-`, `*`, `/`, `&` and `^`. Addition,
subtraction and multiplication keep the low 64 bits of the result and interpret
that word as a signed two's-complement value. This defined assembly wrapping
contract does not permit signed overflow in C. The test model uses unsigned
64-bit arithmetic and copies the result's bit representation into `int64_t`.
AND and XOR operate on all 64 bits. XOR is a bitwise operator here, not a power
operator. OR, remainder and shifts are outside this six-operator project.

Division truncates toward zero. The divisor must be nonzero and the signed
quotient must be representable. `INT64_MIN / -1` violates that requirement.
The command-line caller rejects these two cases before invoking assembly.
The assembly dispatcher also returns zero defensively for those invalid pairs
or an unsupported operator; that fallback is not a successful mathematical
result and must not replace input validation.

Default successful output is exactly:

```text
12 + 5 => 17
12 - 5 => 7
7 * 6 => 42
21 / 3 => 7
42 & 15 => 10
42 ^ 15 => 37
```

The completed program accepts one operator and two signed decimal operands:

```sh
./build/assembly_calculator '+' 12 5
./build/assembly_calculator '/' -21 3
./build/assembly_calculator '&' 42 15
./build/assembly_calculator '^' 42 15
./build/assembly_calculator '+' 4294967308 5
./build/assembly_calculator '+' 9223372036854775807 1
```

These print `result=17`, `result=-7`, `result=10`, `result=37`,
`result=4294967313` and `result=-9223372036854775808`, each with a newline and
exit zero. Quote operators so the shell does not interpret them. Bad arity,
unsupported operators, nondecimal text, out-of-range operands, divisor zero
and signed division overflow produce an explanation on stderr, no successful
result on stdout, and exit 2. For example:

```sh
./build/assembly_calculator '/' 3 0
./build/assembly_calculator '/' -9223372036854775808 -1
```

## Build and acceptance

From the selected `starter` or `solution` directory:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang
cmake --build build
ctest --test-dir build --output-on-failure
./build/assembly_calculator
```

Repeat with GCC using `-DCMAKE_C_COMPILER=gcc` and a separate build directory.
Repeat both compilers with `-DCMAKE_BUILD_TYPE=Release`. Checks use explicit
comparisons rather than `assert`, so Release cannot remove the contract gate.
Direct compilation is also possible:

```sh
cc -std=c17 -Wall -Wextra -Wpedantic -Wconversion -Werror main.c calculator.S -o calculator
cc -std=c17 -Wall -Wextra -Wpedantic -Wconversion -Werror tests.c abi_checks.S calculator.S -o contracts
./contracts
./calculator
```

A completed contract run accepts 12,589 valid expressions and confirms the two
invalid-division guards. Cases include the cross-product of ten fixed values
with all six operators, excluding eleven invalid divisions, followed by 2,000
deterministic operand pairs for every operator. The fixed values include
negative numbers, signed limits, alternating bits and words wider than 32 bits.
The default demo, negative quotient, full-width result and rejected input cases
are separate evidence. Save the starter before comparing its separate reference.

## Register and instruction trace

Under this ABI the left operand arrives in RDI, the right operand in RSI, and
the operator's low byte in DL. The result occupies RAX. Compare DL with each
operator, identify the flags producer for every `je`, and explain why a branch
matches. The arithmetic instructions operate on RAX and RSI at 64-bit width.
An EAX destination clears RAX's upper 32 bits; AX or AL writes preserve the
unwritten high bits. The wide-input case detects an accidental 32-bit path.

For division, copy the signed left operand into RAX and use `cqo` to form the
signed 128-bit dividend in RDX:RAX before `idiv rsi`. The quotient returns in
RAX and the remainder in RDX. DL is part of RDX, so its operator byte is no
longer needed once the division branch is selected. Incorrect dividend setup
can produce a wrong negative quotient or an arithmetic fault. Record that
failure separately from the caller's deliberate rejection of an invalid input.

Inspect the Debug reference with:

```sh
objdump -d -M intel build/assembly_calculator
gdb ./build/assembly_calculator
```

In GDB enter `set disassembly-flavor intel`, `break asm_eval_expression`,
`run`, and `info registers rdi rsi rdx rax rip`. The first readiness probe
uses left 12, right 5 and operator byte 43 (`+`). Step through `cmp`, `je`,
`mov`, `add` and `ret`, or use `finish` to check the returned RAX value 17.
Use `continue` to finish the successful default rows. Repeat with a negative
division case using `set args '/' -21 3`; readiness probes occur before the
requested expression, so continue to the later `/` call with negative RDI.
Addresses vary by run; record observed instruction addresses rather than
copying assumed values.

Completion evidence includes all compiler/profile test results, the six default
rows, a negative quotient, a word wider than 32 bits, rejection of both invalid
divisions, and a trace table showing arguments, operator comparison, chosen
branch, result and return. A copied experiment that changes an AND path to OR,
uses a 32-bit operand move, omits signed-dividend setup or clobbers RBX must fail
the native contracts. Restore the correct implementation before acceptance.
