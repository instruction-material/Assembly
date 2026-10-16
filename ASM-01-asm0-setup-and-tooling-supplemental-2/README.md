# A definition that the linker cannot see

This optional setup transfer activity follows the required mixed C/assembly
project. Identify the boundary between assembling a function and making that
function available to another object file. Keep this activity's learner and
reference work separate from the required setup attempt.

## Read the object boundary

The C caller declares `lab_answer` and expects its implementation in another
object. The assembly file contains that label, but its learner version omits
the global-binding directive. An assembler can produce a valid object with a
local function symbol while a separate C object still has an unresolved global
reference. Successful assembly therefore does not establish successful linking.

GNU assembly's `.globl lab_answer` makes this definition available to the linker
outside its own object. It does not change the function's return instruction or
invent a second implementation. On Linux x86-64 using the System V AMD64 ABI,
this small function returns an integer through EAX. The supplied routine does
not allocate a stack frame or modify callee-saved registers; `ret` consumes the
caller's return address.

The source uses GNU AT&T notation: `movl $LAB_VALUE, %eax` writes a
32-bit immediate into EAX, with the source operand first. The guide's Intel
disassembly view puts the destination first: the completed default instruction
is `mov eax,0x2a`. These are two renderings of the same emitted instruction.

## Environment and files

Use an owned Linux x86-64 VM or WSL environment with CMake 3.20+, GCC or Clang,
and binutils (`nm`, `readelf`, `objdump`). This pack uses ELF symbols and GNU
assembly syntax. The browser workspace edits and exports the files; native
building and object inspection take place in that Linux environment.

Each role contains `main.c`, `routine.S`, `lab.h`, `tests.c`, `CMakeLists.txt`
and `trace.md`. The shared README is this full guide. The C caller prints the
returned integer and checks it against the configured value. The contract
program supplies a separate caller; the worksheet records the build evidence.

## Predict and retain the unfinished build

From the exported project root, configure and build the learner role:

```sh
cc --version
cmake -S starter -B build-symbols-first -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-symbols-first --verbose
```

The initial link fails on the missing externally visible `lab_answer` definition.
Keep that diagnostic. GCC can be used by changing both compiler options to
`gcc` and selecting another build directory. Replace `clang` with `gcc` in the
direct stage commands as well. Do not repair the C caller or add
a second C implementation to hide the missing assembly definition.

Inspect the stages separately from the learner role directory:

```sh
cd starter
mkdir object-first
clang -std=c17 -Wall -Wextra -Wpedantic -Werror -c main.c -o object-first/main.o
clang -c routine.S -o object-first/routine.o
nm -P object-first/main.o
nm -P object-first/routine.o
readelf -Ws object-first/routine.o
objdump -dr -Mintel object-first/routine.o
clang object-first/main.o object-first/routine.o -o object-first/app
```

The last command reproduces the link failure. Compare the caller's undefined
symbol with the routine's local function definition. In GNU `nm` output,
lowercase `t` identifies a local text symbol and uppercase `T` a global text
symbol. Use the `readelf` binding column as a second view. Record the actual
symbol spelling and raw diagnostic instead of assuming every undefined-symbol
error has this cause.

## Make one directive repair

Replace the `TODO` comment in `routine.S` with `.globl lab_answer`, leaving the
function body and caller unchanged. From the project root, use a fresh build:

```sh
cmake -S starter -B build-symbols-fixed -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-symbols-fixed --verbose
ctest --test-dir build-symbols-fixed --output-on-failure
./build-symbols-fixed/app
```

The default output is `answer=42`. Repeat the object inspection and compare the
same function's global binding with the original local binding. Explain why the
link result changed while the return instruction kept the same purpose.

Configure another fresh build with `-DLAB_VALUE=73`, then run and test it. The
output becomes `answer=73`; this changes the configured return value and leaves
the object-boundary explanation intact. Values outside 0 through 255 are refused
by the supplied configuration. Keep compiler, role and configuration changes
separate in the worksheet.

## Completion and review

Complete `trace.md` with the failed link, both object symbol views, the minimal
repair, successful native output and changed-value run. Compare the reference
only after recording an independent diagnosis. Its only role-specific source
change is the global-binding directive. Code checks do not complete the worksheet.

If linking still fails, retain the exact command and check which object defines
the requested spelling, whether that definition is global, and whether that
object was included. A stale build or a differently named function is a separate
case. Retain separate fresh build directories and record each command's status.
An older executable does not prove that changed source compiled and linked
successfully.

References: [GNU symbol visibility](https://sourceware.org/binutils/docs/as/Global.html)
and [GCC compilation stages](https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html).
