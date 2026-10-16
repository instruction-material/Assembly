# Variable-Count 64-Bit Shifts

This optional extension compares left, logical-right and arithmetic-right
shifts from the same original value. It adds effective count masking and sign
filling to the unit's arithmetic/logic work. Each stage reloads the original
value, so its output describes one operation on that input.

## Interface, count and result

`lab_operation(initial, incoming, output)` receives the value in RDI, raw count
in RSI and a valid owned output pointer in RDX. The caller allocates a 32-byte
LabResult: left at offset 0, logical-right at 8, arithmetic-right at 16 and
effective-count at 24. Each field is eight bytes. Preserve RBX, RBP, R12 through
R15, the stack and return address.

The first three stages load RAX from RDI and RCX from RSI, then use CL as the
count operand. With these 64-bit instructions the effective count is the low
six count bits, equivalent to incoming modulo 64. Counts 0 and 64 leave the
original value; 1 and 65 select the same one-bit shift. The last slot records
the effective count. This instruction masking is explicit in the C model,
which obtains an in-range count before evaluating any unsigned-C shift.

SHL inserts low zeros and discards bits outside the result. SHR inserts high
zeros. SAR fills the high end with the original sign bit. The C model constructs
that sign fill with unsigned masks, avoiding reliance on signed-C right-shift
behavior. This output interface reports values and count. Keep observed shift
flags separate, without treating undefined bits as a portable contract.

## Predict normal, changed and boundary counts

The default initial value is 8000000000000003 and raw count is decimal 33
(hexadecimal 21). A 32-bit count mask would incorrectly turn 33 into one.
The changed input is fffffffffffffff7, interpreted as signed -9, with raw
count decimal 65 (hexadecimal 41), giving an effective count of one.

| Field | Default | --changed |
| --- | --- | --- |
| left | 0000000600000000 | ffffffffffffffee |
| logical-right | 0000000040000000 | 7ffffffffffffffb |
| arithmetic-right | ffffffffc0000000 | fffffffffffffffb |
| effective-count | 0000000000000021 | 0000000000000001 |

SAR of the changed negative value gives signed -5. Its rounding toward negative
infinity differs from the arithmetic project's IDIV, where -9 divided by two
truncates toward zero to -4. For all-one input and count 63, predict
left=8000000000000000, logical-right=1 and arithmetic-right=ffffffffffffffff.
Also compare counts 0, 1, 32, 63, 64, 65 and 255, retaining the effective count.

## Correct and trace the signed shift

The `SHIFT_SIGNED` task uses logical-right in the arithmetic-right slot. Select
the instruction matching that slot's sign contract. Left shift, logical-right,
count calculation, model, caller and tests remain unchanged.

In GDB use `set disassembly-flavor intel`, `break lab_stage2`, and `run`.
Record RAX, RCX, RSI and the current instruction, step once with `si`, then
record the result. Step its store and use `x/gx ($rdx+16)`. Compare untouched
and corrected results for the same raw count. Repeat `run --changed` and
explain both sign fill and effective count. At lab_stage3 trace the count
calculation into its output slot. Retain actual addresses and instructions.

In an owned corrected copy, insert `and ecx, 31` after only the first stage's
count load. That stage now uses one for the default count, so its left result
disagrees with the unchanged six-bit-count model. Retain the first failed
field, explain the width assumption, then remove the added mask.

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
