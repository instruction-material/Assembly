# Arithmetic Results, Implicit Registers and Defined Flags

Assembly Unit 3 follows arithmetic as observable machine state. The project
implements two unfinished instruction sequences, checks nine operations and
records the result registers and status bits that each operation actually
defines. It differs from the integer calculator's command evaluation: the main
deliverable here is a correct value/status contract and an explanation of carry,
signed overflow, implicit operands, rejected divisions and compiler output.

## Target and files

Use Linux x86-64 and the System V AMD64 ABI, GNU/Clang Intel-syntax assembly,
C17, CMake 3.20+, Clang or GCC, GDB and binutils. An x86-64 Linux VM or lab is
required on macOS; Windows can use an x86-64 WSL distribution. ARM64 instructions,
Mach-O and Windows x64 calling conventions are separate targets. The browser
workspace edits and saves source; native execution belongs to the Linux lab.

Each role includes routine.S, arithmetic.h, model.c, main.c, tests.c,
abi_checks.S, fault.S, fault.c, CMakeLists.txt and trace.md. Keep these files
together under starter/ or solution/ beside this shared guide. model.c supplies
an unsigned-C value/status oracle; the tests and ABI wrapper remain unchanged.
fault.S and fault.c form a deliberately separate fault probe. The ordinary
arithmetic function guards its division operations and does not invoke that
probe.

## Read the interface before coding

`arithmetic_eval(op, left, right, out)` receives an operation number in EDI,
64-bit operand patterns in RSI/RDX and a writable result pointer in RCX. It
returns one in EAX after filling a 32-byte ArithmeticResult. Its four eight-byte
fields are value, auxiliary, flags and defined at offsets 0, 8, 16 and 24.
The caller owns valid writable output storage. A null pointer, operation outside
0..8, divisor zero or signed minimum divided by minus one returns zero without
changing output. These checks do not establish that every non-null pointer is
valid. Preserve RBX, RBP, R12 through R15, the stack and return address.

| op | Instruction | value | auxiliary | Reported flag mask |
| --- | --- | --- | --- | --- |
| 0 | ADD | low 64-bit sum | zero | CF, ZF, SF, OF |
| 1 | SUB | low 64-bit difference | zero | CF, ZF, SF, OF |
| 2 | one-operand IMUL | low product word | high signed product word | CF, OF |
| 3 | IDIV | signed quotient bits | signed remainder bits | none |
| 4 | AND | bitwise conjunction | zero | CF, ZF, SF, OF |
| 5 | OR | bitwise union | zero | CF, ZF, SF, OF |
| 6 | XOR | differing bits | zero | CF, ZF, SF, OF |
| 7 | TEST | unchanged left operand | zero | CF, ZF, SF, OF |
| 8 | CMP | unchanged left operand | zero | CF, ZF, SF, OF |

The contract uses masks CF=0x1, ZF=0x40, SF=0x80 and OF=0x800. The full reported
mask is 0x8c1; multiplication reports 0x801. Unreported bits are zero in the
result object. A zero mask after division means the result makes no flag claim,
rather than claiming that the processor's flags are all zero. PF and AF are
outside this interface. TEST computes flags from left AND right without changing
left; CMP computes flags from left minus right without storing that difference.

## Predict carry and signed overflow separately

An eight-byte destination retains 64 bits. Unsigned UINT64_MAX plus one wraps
to zero, producing carry and zero. Signed INT64_MAX plus one has the minimum
signed pattern, producing signed overflow and a sign bit without unsigned
carry. Both results are explainable from the same fixed-width bit operation.
CF tracks unsigned carry or subtraction borrow; OF concerns the representable
signed range. ZF describes a zero result and SF copies the result's high bit.

For subtraction, zero minus one produces all-one bits with borrow, while signed
minimum minus one produces the maximum signed pattern with signed overflow.
Keep a value's bit pattern separate from its signed or unsigned interpretation.
An unsigned below condition after CMP reads CF; a signed less condition reads
SF different from OF. The default CMP of signed minimum against one illustrates
why the raw sign bit alone cannot replace a signed comparison. Unit 4 applies
these producers and condition codes to longer control-flow paths.

AND, OR and XOR set the relevant zero/sign observations from their result and
clear CF and OF. TEST has the same reported flag interpretation for its
temporary AND result. Instructions used to dispatch the operation also modify
flags. Capture the arithmetic instruction's flags immediately, before a later
comparison, masking operation or register-clearing XOR overwrites them.
The supplied pushfq/pop sequence snapshots them; it then masks the saved value,
rather than treating the mask instruction's new flags as the arithmetic result.

## Complete multiplication and signed division

Only ARITH_MUL and ARITH_DIV in routine.S are unfinished. ADD, SUB, logic, TEST,
CMP, argument validation and result storage provide the surrounding baseline.
Complete the two named regions and keep the model, driver and tests unchanged.

The one-operand `imul r8` multiplies signed RAX by R8 and places the full
128-bit product in RDX:RAX. The auxiliary field retains RDX. CF and OF indicate
whether the full product fits as the sign extension of its low word. Other
arithmetic flags from IMUL are not part of this contract. In contrast, the
two-operand form retains only the destination-width low product; it cannot
supply this interface's high word. Predict signed minimum times minus one:
the positive mathematical product is 2^63, with high word zero and low word
0x8000000000000000, so it overflows the signed 64-bit range.

For IDIV, the dividend is the signed 128-bit RDX:RAX pair. Sign-extend the
64-bit left operand into that pair, commonly using CQO, before dividing by R8.
The quotient replaces RAX and the remainder replaces RDX. Quotients truncate
toward zero and a nonzero remainder has the dividend's sign. For -21 divided
by 4, predict quotient -5 and remainder -1; with 21 divided by -4, predict -5
and +1. Clearing RDX is appropriate for some unsigned divisions but does not
sign-extend a negative signed dividend. No status flag after IDIV is used to
establish a result or branch condition in this project.

The public guards reject divisor zero and signed minimum divided by minus one
before IDIV. Correct sign extension makes every other signed 64-bit pair fit
the quotient range. A syntactically valid IDIV instruction can still fault
when its implicit dividend is wrong. The separate probe below demonstrates the
two deliberately unguarded fault cases in owned child processes.

## Build and retain the first failure

From the extracted project root:

```sh
cmake -S starter -B build-O0 -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_C_FLAGS_DEBUG="-O0 -g" -DCMAKE_ASM_FLAGS_DEBUG="-O0 -g" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build-O0 --verbose --parallel 1
./build-O0/assembly_arithmetic
ctest --test-dir build-O0 --output-on-failure
```

The untouched starter builds, but the demo exits 78 without successful result
rows and the unchanged contracts fail. Retain that evidence. After completing
only the named routine regions, repeat the same commands, then run
`./build-O0/assembly_arithmetic --changed`. A completed demo prints nine operation
rows and one C-helper row. Each row includes the operand patterns, two result
words, captured flags and the reported mask. Arithmetic disagreement exits one;
unsupported command arguments exit two with usage and no result rows. Passing
code does not complete trace.md.

The unchanged native contracts exercise all 65,536 pairs of sign-extended
eight-bit inputs for all nine operations, full-width boundary pairs, invalid
operations, rejection without output writes, a null output and six preserved
registers. This is a broad reproducible set, not an exhaustive proof over all
64-bit operand pairs. The C oracle uses unsigned arithmetic and 32-bit limbs
for the product high word, then adjusts it for signed operands. It avoids signed
C overflow. Native acceptance also compares actual assembly outputs against a
separate arbitrary-precision Python model, including changed full-width cases.

## Observe the actual instructions

Disassemble the completed program and start GDB:

```sh
objdump -d -M intel --disassemble=arithmetic_eval build-O0/assembly_arithmetic
gdb ./build-O0/assembly_arithmetic
```

In GDB, break at arithmetic_add_step, run, record RAX/R8 and the next
instruction, then use `si` and `info registers rax eflags`. Record the actual
address and the masked CF/ZF/SF/OF values. Break at arithmetic_multiply_step
before its IMUL and repeat with RDX/RAX before and after. At
arithmetic_divide_step, the preceding sign extension has prepared the dividend;
record RDX, RAX and R8, step IDIV and retain the quotient and remainder.
Classify its flags as undefined for this contract. Repeat using `run --changed`
to distinguish carry/zero from signed overflow and positive from negative
remainder. Do not copy reference addresses into the current build's trace.

For the isolated fault experiment, keep core dumps disabled in the current lab
shell and use the separately named executable:

```sh
ulimit -c 0
./build-O0/arithmetic_fault_probe negative
gdb --args ./build-O0/arithmetic_fault_probe zero
```

In that GDB session, break at arithmetic_fault_step, run, inspect RDX/RAX/RSI,
then step the actual IDIV. Record the integer divide error reported as SIGFPE.
Repeat in a separate process using the overflow argument. The first pair has
divisor zero; the second has a correctly extended minimum dividend and divisor
minus one but an unrepresentable quotient. The public function rejects those
pairs; the probe intentionally omits those guards. Keep each probe separate
from the ordinary successful contract run. No host signal policy, global core
setting or external program needs changing.

The C oracle, demo and ordinary contracts keep undefined-behavior sanitization
enabled. The separately linked fault probe deliberately omits that runtime so
the experiment observes the kernel SIGFPE directly; Clang's sanitizer handler
otherwise diagnoses the native divide error and exits one. This target-specific
control changes neither the public guards nor the normal C checks.

## Compare one C helper at O0 and O2

The separate C helper returns `(left + right) ^ (left & right)` using uint64_t
operations. Addition therefore has a defined low-word result. It does not
promise the flags of a literal instruction sequence. Generate real compiler
listings and compare the arithmetic_c_mix body, keeping its function boundary
and actual compiler version beside the observations:

```sh
mkdir -p observed
clang -std=c17 -O0 -g -S -masm=intel starter/model.c -o observed/model-O0.s
clang -std=c17 -O2 -g -S -masm=intel starter/model.c -o observed/model-O2.s
cmake -S starter -B build-O2 -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_C_FLAGS_RELEASE="-O2 -g -DNDEBUG" -DCMAKE_ASM_FLAGS_RELEASE="-O2 -g -DNDEBUG" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build-O2 --verbose --parallel 1
ctest --test-dir build-O2 --output-on-failure
./build-O2/assembly_arithmetic --changed
```

The -S compiler option stops before assembly/linking; the lowercase .s output
is compiler-generated text, distinct from the handwritten preprocessed .S
input. Map the helper's argument movement, sum, mask and XOR in the actual
listings. Explain observed changes or unchanged operations without requiring a
particular mnemonic sequence or inferring speed from instruction count.
Repeat with both CMake compiler options and the listing command set to GCC,
using separate directories. Reference builds use solution/ and separate output
folders. Unit 9 develops compiler analysis further; Unit 11 measures timing.

## Complete the evidence record

trace.md contains predictions, actual result/flag observations, the full
multiply/divide register traces, rejected public calls, separate fault-process
evidence, compiler listings, a changed input and limits. Preserve the initial
exit-78 result and first prediction before consulting the reference. Independent
work follows predict, build, inspect, test and explain. A paced walkthrough
pauses at the flag-producing instruction, the implicit dividend and the first
fault before revealing the next state. Both formats use the same completed
evidence, with runtime correctness and explanation checked separately.

Instruction definitions are in the [Intel architecture manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html),
including the [Volume 2A instruction reference](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf).
Compiler options are documented in [GCC overall options](https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html)
and [x86 assembly dialect options](https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html).
