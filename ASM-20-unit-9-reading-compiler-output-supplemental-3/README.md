# Pointer Aliasing and Reload Decisions

## Exact contract and predictions

The ordinary helper adds delta to `*left`, XORs the resulting `*left` into
`*right`, and returns the final `*left`. Arithmetic is uint64_t modulo 2^64.
The restricted helper has the same statements with two restrict-qualified
pointer parameters. Its callers must supply distinct objects for this task,
which reads and modifies both objects. No test violates that requirement.

The operation owns two independent two-word arrays, each initially
`{initial, incoming}`. The ordinary helper uses the first array: left is slot 0,
right is slot 0 when initial is odd or slot 1 when initial is even, and delta is
incoming. The restricted helper always uses the two distinct slots of the
second array. Inputs are integers, never arbitrary addresses.

Outputs are the ordinary return, its final slot 0, its final slot 1, the restricted
return and its final right slot. For default inputs 3 and 5 the ordinary pointers
alias: 3 + 5 becomes 8, then 8 XOR 8 becomes 0; the untouched second slot remains 5.
The restricted call has separate objects: its return is 8 and right is5 XOR 8 = d.
The five hexadecimal words are:

`0000000000000000 0000000000000000 0000000000000005 0000000000000008 000000000000000d`

`--changed` uses 2 and 5, making the ordinary objects disjoint. Outputs are
`0000000000000007 0000000000000007 0000000000000002 0000000000000007 0000000000000002`.
Also predict zero, UINT64_MAX+1 wraparound and an odd initial with zero incoming.

The compiler must preserve the ordinary helper's behavior for both valid alias
patterns. The restricted call provides a stronger access contract and may allow
the compiler to retain a value across the right-hand store. Observe actual
reloads and store order at -O0 and -O2. Neither fewer instructions nor a particular
reload count is guaranteed. Equal pointers must never be passed to the restricted
helper in this task; sanitizer success would not validate that promise.

For the controlled regression, replace only the ordinary body in a disposable
reference copy with `uint64_t cached = *left + delta; *left = cached;
*right ^= cached; return cached;`. This remains defined C but returns the earlier
value after an aliased XOR. The default rejects it; the disjoint changed case
still agrees. The restricted helper and model remain unchanged.

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
printf '3 5\n2 5\nffffffffffffffff 1\n' | ./build-O0/contracts --rows
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
