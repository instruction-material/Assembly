# Signed and Unsigned Comparison Decisions

The required arithmetic project records results and defined flag snapshots.
This optional transfer project turns a CMP snapshot into six actual decisions.
The same two bit patterns can give opposite signed and unsigned decisions.

## Interface and flag producer

`lab_operation(initial, incoming, output)` receives two 64-bit patterns in
RDI/RSI and a valid owned output pointer in RDX. The caller allocates a 48-byte
LabResult. Write six eight-byte zero/one fields at offsets 0, 8, 16, 24, 32 and
40. Preserve RBX, RBP, R12 through R15, the stack and return address.

Every stage starts with `cmp rdi, rsi`, computing flags for initial minus
incoming without replacing either operand. `mov eax, 0` then prepares a
full-width zero while retaining those flags. SETcc changes AL to zero or one,
and the next instruction stores all of RAX. An AL write alone would leave
unrelated upper bits. An XOR used to clear EAX would replace CMP's flags.

| Field | Instruction | Condition from CMP |
| --- | --- | --- |
| unsigned-below | SETB | CF=1 |
| unsigned-below-equal | SETBE | CF=1 or ZF=1 |
| signed-less | SETL | SF differs from OF |
| signed-less-equal | SETLE | ZF=1 or SF differs from OF |
| equal | SETE | ZF=1 |
| not-equal | SETNE | ZF=0 |

Unsigned ordering uses 0 through 2^64-1. For signed interpretation, a pattern
at least 2^63 represents that pattern minus 2^64. Equality has the same result
under either interpretation. The C model flips each sign bit before comparing
signed order, keeping every calculation within unsigned types.

## Predict complete rows

The default operands are 8000000000000000 and 0000000000000001. The left
operand is signed -2^63 or unsigned 2^63. Subtraction wraps to
7fffffffffffffff, with CF=0, ZF=0, SF=0 and OF=1. Signed less is true despite
the clear SF. The changed pair reverses these operands: SF=1 and OF=1 then
give signed-less=false and unsigned-below=true.

| Field | Default | --changed |
| --- | --- | --- |
| unsigned-below | 0000000000000000 | 0000000000000001 |
| unsigned-below-equal | 0000000000000000 | 0000000000000001 |
| signed-less | 0000000000000001 | 0000000000000000 |
| signed-less-equal | 0000000000000001 | 0000000000000000 |
| equal | 0000000000000000 | 0000000000000000 |
| not-equal | 0000000000000001 | 0000000000000001 |

For one against one, predict below=0, below-equal=1, less=0, less-equal=1,
equal=1 and not-equal=0. Keep the producer flags next to each decision.

## Correct and trace the signed decision

The `COMPARE_SIGNED` task uses unsigned-below for the signed-less slot. Select
the condition matching that slot's interpretation. The other stages, zero
preparation, stores, model, caller and tests form the unchanged baseline.

In GDB use `set disassembly-flavor intel`, `break lab_stage2`, and `run`.
Record RDI, RSI, RAX and EFLAGS, step the SETcc with `si`, then record its
decision and unchanged CMP-produced flags. Step the store and use
`x/gx ($rdx+16)`. The default reference stores one; the original task stores
zero. Repeat `run --changed` and retain current addresses beside their meanings.

In an owned corrected copy, replace only the signed-less stage's `mov eax, 0`
with `xor eax, eax`. Both clear the destination, but the latter replaces the
producer flags. The minimum signed pattern against one requires signed-less=1,
so the unchanged contract rejects that copied regression. Explain which
producer its SETL observes, retain the failed case, then restore MOV.

## Build and retain the first result

Use ordinary-user Linux x86-64, the System V AMD64 ABI, GNU Intel-syntax
assembly, C17, CMake 3.20+, Clang or GCC, GDB and binutils. On macOS use an
x86-64 Linux VM or lab; on Windows use an x86-64 WSL distribution. The browser
workspace edits and saves source. Compile and debug the export in that lab.

Each role contains routine.S, main.c, lab.h, model.c, tests.c, abi_checks.S,
CMakeLists.txt and trace.md, with shared README.md beside the role folders.
Keep all nine selected files together. From the extracted root:

```sh
cd starter
cmake -S . -B build-Debug -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-Debug --verbose --parallel 1
./build-Debug/app
ctest --test-dir build-Debug --output-on-failure
```

The untouched app builds but exits 78 without successful rows, and its
contracts fail. Preserve that observation before correcting the named
instruction in routine.S. Keep main.c, lab.h, model.c, tests.c and abi_checks.S
unchanged. Repeat the commands after the repair, followed by:

```sh
./build-Debug/app --changed
cmake -S . -B build-Release -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-Release --verbose --parallel 1
ctest --test-dir build-Release --output-on-failure
./build-Release/app --changed
```

Repeat both profiles with both CMake compiler options set to GCC and separate
directories. Reference builds use solution/ and separate directories. Their
unchanged contracts and both demonstrations pass. Unknown arguments exit 64
with usage and no result rows.

The contracts compare 256 fixed pairs plus 10,013 deterministic pairs with the
unsigned-C model, checking every output and six preserved registers. Explicit
comparisons remain active in Release. Success prints `10269 independent logic cases` with the field count. These inputs provide repeatable coverage rather
than enumerating every 64-bit pair. Native validation also uses a separate
Python oracle, different generated inputs and a different formulation.

## Inspect actual instructions and complete the record

```sh
objdump -d -M intel --disassemble=lab_operation build-Debug/app
readelf -Ws build-Debug/CMakeFiles/app.dir/routine.S.o
gdb ./build-Debug/app
```

In trace.md retain target/compiler versions, commands, actual addresses,
operands, predictions, registers before and after each instruction, stored
words and explanations. Use the lab_stage labels, repeat --changed and a
boundary pair from tests.c, and retain the rejected copied regression described
below before restoring correct source. Passing code does not fill this record.

Independent work follows predict, build, inspect, test and explain. A paced
walkthrough pauses at the same producer, operation and store before discussing
the next state. Both retain the initial failure, minimal repair, GCC/Clang
Debug/Release checks, demonstrations, changed condition and explained trace.
Preserve learner and reference attempts separately and export the saved
routine.S and trace.md together.

## Instruction references

[Intel's architecture manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
define the instructions. The [Volume 2B reference](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf)
contains SETcc and SAL/SAR/SHL/SHR. Check the actual 64-bit operand form. The
worked cases, models, contracts and observation tasks here belong to this lab.
