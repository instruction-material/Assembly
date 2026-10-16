# Assembly input language and preprocessing evidence

This optional setup extension follows the required toolchain project. Diagnose
a build that sends preprocessor-dependent assembly directly to the assembler.
Keep its own learner and reference attempts separate from the required setup
project and the symbol-visibility transfer activity.

## Follow the selected input language

The supplied `routine.S` includes `lab.h` and uses the `LAB_VALUE` macro as an
immediate operand. An uppercase `.S` filename normally selects assembly with
preprocessing. The compiler driver's explicit `-x` option overrides suffix-based
language selection. The learner CMake configuration deliberately selects
`assembler`; the reference selects `assembler-with-cpp`.

With preprocessing disabled, the include directive is treated as an assembly
comment and the macro name remains unresolved. This can still produce an
object with a relocation against `LAB_VALUE`, followed by a link failure. The
stage that reports a failure need not be the stage where the wrong choice was
made. Here `lab_answer` is already global in both roles, so adding another
global directive does not resolve the macro.

The source uses GNU AT&T notation: `$` marks an immediate and `%eax` names
the 32-bit destination register. After preprocessing, `movl $41, %eax` appears
as `mov eax,0x29` in the guide's Intel disassembly view. Source and destination
order differ between the two notations; the emitted instruction is the same.

## Environment and files

Use an owned Linux x86-64 VM or WSL environment, CMake 3.20+, GCC or Clang and
binutils (`nm`, `readelf`, `objdump`). The source uses ELF and GNU assembly
syntax. Building and object inspection take place in that environment; the
browser workspace edits, saves and exports the project.

Each role contains `main.c`, `routine.S`, `lab.h`, `tests.c`, `CMakeLists.txt`
and `trace.md`, plus the shared complete README. The header defines a default
value and a C declaration guarded from assembly input. The C caller prints the
actual return value; the second caller tests it. No Python programming is needed.

## Observe the original selection

From the exported project root:

```sh
cmake -S starter -B build-language-first -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-language-first --verbose
```

Keep the failing diagnostic and the actual command compiling `routine.S`.
The learner cache selects `LAB_ASM_LANGUAGE=assembler`. Examine
`build-language-first/compile_commands.json` to find that explicit language
argument. Use another directory when selecting GCC instead of Clang.

From the learner role directory, compare the stages directly:

```sh
cd starter
mkdir language-first
clang -E -P -x assembler-with-cpp routine.S -o language-first/preprocessed.s
clang -x assembler -c routine.S -o language-first/raw.o
nm -P language-first/raw.o
readelf -r language-first/raw.o
objdump -dr -Mintel language-first/raw.o
clang -std=c17 -Wall -Wextra -Wpedantic -Werror -c main.c -o language-first/main.o
clang language-first/main.o language-first/raw.o -o language-first/app
```

The final link fails. Read the actual preprocessed text, unresolved macro symbol
and relocation together. The routine's global function symbol is distinct from
the unresolved `LAB_VALUE` symbol. Preserve both instead of inferring a missing
function from an unspecified link error.

## Correct the language and rebuild

Change the learner CMake default for `LAB_ASM_LANGUAGE` to
`assembler-with-cpp`. Use a fresh directory because a CMake cache retains its
previously selected value. From the project root:

```sh
cmake -S starter -B build-language-fixed -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-language-fixed --verbose
ctest --test-dir build-language-fixed --output-on-failure
./build-language-fixed/app
```

The output is `answer=41`. Compare the executed compiler arguments, preprocessed
numeric operand and object relocation listing with the unfinished build. Explain
which observation supports the preprocessing diagnosis. The learner and reference
files differ only in this default input-language selection.

Configure another fresh build with `-DLAB_VALUE=73`. Its output is `answer=73`.
Compare the changed numeric operand and successful native result while leaving
the selected preprocessing language fixed. Values outside 0 through 255 are
refused by the supplied configuration.

## Completion and troubleshooting

Complete `trace.md` with predictions, the original failing build, actual compiler
arguments, preprocessed text, object symbols/relocations, the minimal configuration
repair and the changed-value run. Compare the reference after making an independent
diagnosis. Passing code tests does not finish the worksheet.

If a changed source default appears ineffective, inspect the actual CMake cache
and commands and choose a new build directory. If preprocessing succeeds but the
link still fails, examine the remaining symbol and object-file evidence separately.
Do not use an older executable as the result of a build that failed.

References: [GCC input languages and stages](https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html)
and [CMake per-source compile options](https://cmake.org/cmake/help/latest/prop_sf/COMPILE_OPTIONS.html).
