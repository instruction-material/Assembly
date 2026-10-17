# Byte Promotions and Signed Comparisons

## Exact contract and predictions

The selected byte is `(incoming >> (8 * (initial & 7))) & 255`. Its eight bits
are copied into an exact-width int8_t object. The threshold is
`((initial >> 8) & 255) - 128`, calculated as an int. Outputs are the byte index,
the signed value encoded as a uint64_t, the unsigned value, and the signed and
unsigned-byte comparison results (each 0 or 1). The header requires eight-bit
bytes and a 32-bit int. All inputs are unsigned 64-bit values.

Both byte types promote to int for these comparisons because int represents
their complete ranges. A uint8_t operand therefore does not make this comparison
an unsigned-int comparison. The signed byte retains its negative value; the
unsigned byte has a value from 0 to 255. The provided C code separates the source
bit representation from the comparison. It does not convert an out-of-range
unsigned value to a signed integer by a cast.

The default inputs 8007 and 80ff7f0100fe0281 select byte 80 with threshold 0.
The five output words are:

`0000000000000007 ffffffffffffff80 0000000000000080 0000000000000001 0000000000000000`

`--changed` uses two zero inputs: the threshold is -128, and all five words are
zero. Also predict bytes 7f, 80 and ff at thresholds -1, 0 and 127. In a separate
reference copy replace the signed helper's comparison with
`return (uint8_t)value < threshold;`. This is a defined conversion but changes
the contract for negative signed bytes. Record a rejected case and a case that
still agrees. Keep the unsigned helper and model unchanged.

## Working baseline and observation task

Both role programs already work. Complete analysis.md with predictions and real
compiler/debugger evidence. The separate reference supplies portable reasoning;
its addresses and machine instruction choices must be recorded from the current
build. The required Unit 9 score project follows one arithmetic function through
the toolchain; this optional investigation examines the stated type or alias
contract across optimization levels.

Use ordinary-user Linux x86-64, the System V AMD64 ABI, C17, Clang or GCC,
CMake 3.20+, GDB and binutils. On macOS use an x86-64 Linux lab/VM; on Windows use
an x86-64 WSL distribution. Each role contains baseline.c, operation.c, main.c,
lab.h, model.c, tests.c, abi_checks.S, CMakeLists.txt and analysis.md. The roles
differ only in analysis.md. Keep README.md one level above the selected role.

baseline.c contains the inspected functions. operation.c calls them from a
separate translation unit, without link-time optimization, so actual function
entry and return observations remain available in both builds. model.c checks
the same five-word contract through independent arithmetic. tests.c also calls
the supplied six-register ABI probe; explicit checks remain active in Release.

From the selected role directory:

```sh
cmake -S . -B build-O0 -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_C_FLAGS_DEBUG="-O0 -g"
cmake --build build-O0 --verbose --parallel 1
ctest --test-dir build-O0 --output-on-failure
./build-O0/app
./build-O0/app --changed
cmake -S . -B build-O2 -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_C_FLAGS_RELEASE="-O2 -g -DNDEBUG"
cmake --build build-O2 --verbose --parallel 1
ctest --test-dir build-O2 --output-on-failure
mkdir -p observed
clang -std=c17 -O0 -g -S -masm=intel -fverbose-asm baseline.c -o observed/baseline-O0.s
clang -std=c17 -O2 -g -S -masm=intel -fverbose-asm baseline.c -o observed/baseline-O2.s
objdump -d -M intel build-O0/app > observed/linked-O0.txt
objdump -d -M intel build-O2/app > observed/linked-O2.txt
gdb ./build-O0/app
```

Repeat with GCC in separate build directories, recording `clang --version` or `gcc --version` and
all flags. The two source listings are assembler input, whereas objdump shows
the linked program's instructions and addresses. Comments and directives are
not executed instructions. The ordinary contracts check 10,269 fixed and
deterministic pairs. Additional native verification compares actual result rows
with a Python integer/owned-object model and assembles and executes the generated
listings. Unsupported app arguments exit 64; a changed-contract mismatch exits 78.

## Independent input cases

`contracts --rows` accepts pairs of unsigned hexadecimal tokens, each one to
sixteen digits without a sign or 0x prefix. Whitespace separates tokens. Each
output row contains the ABI preservation flag (1 means the six saved registers
were preserved) followed by the five actual hexadecimal result words. Compare
those words with the predictions; row mode reports observations rather than
grading the worksheet. Malformed, oversized or incomplete token pairs exit 64.

```sh
printf '8000 80\n8000 ff\nff00 7f\n' | ./build-O0/contracts --rows
```

In GDB set disassembly-flavor intel and break at the inspected function's entry.
Record actual argument widths, PC, RSP and the return word at entry, then step
its instructions through RET. Verify the returned value at the declared width,
the caller PC and RSP after return. For pointer functions record both valid owned
addresses and the pointed-to words before/after stores. Repeat on the optimized
binary; do not copy addresses or assume source-line stepping has the same shape.

Retain TARGET, PREDICT, TYPES, MAP, OPTIMIZE, TRACE and REGRESSION evidence in
analysis.md. Keep the provided C and ABI code unchanged outside the separate
controlled-regression copy. Test success does not complete the observation task.

References: [WG14 C draft N1570](https://open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf),
sections 6.3.1.1, 6.3.1.3, 6.7.3.1 and 7.20.1.1. The project compiles as C17.
