# Unit 9: Reading Compiler Output

Follow a complete C function through real compiler-generated assembly and linked object instructions. Compare -O0 and -O2 with identical input/output contracts and explain the differences using actual evidence. This is an observation and analysis project. Both role programs already work; the learner completes starter/analysis.md. A successful build or run alone is not project completion.

## Target, tools and files

Use Linux x86-64 and the System V AMD64 ABI, C17, Clang or GCC, CMake 3.20 or later, GDB and objdump. Use an x86-64 Linux VM/lab on macOS, or an x86-64 WSL distribution on Windows. Record uname -s, uname -m and compiler --version before comparing output. Clang/GCC listings and debug locations can differ by version; record the actual build rather than copying assumed addresses.

Each independent role folder has model.c, model.h, main.c, tests.c, abi_checks.S, CMakeLists.txt and analysis.md. model.c is the supplied C baseline and abi_checks.S is an unchanged test helper. The learner worksheet has named prediction, mapping, optimization, changed-case and trace sections. The separate solution worksheet supplies portable explanations and a changed-case example, not a fabricated universal compiler listing.

## Exact C and machine contract

```c
int64_t compiled_score(int64_t value, int64_t factor, int64_t bias);
```

All three signed 64-bit inputs are valid. Compute value*factor+bias modulo 2^64 and interpret the final bits as signed. The implementation uses uint64_t arithmetic followed by memcpy into int64_t, avoiding signed C multiplication/addition overflow. Argument registers at integer function entry are RDI, RSI and RDX; return through RAX. Preserve RBX, RBP and R12 through R15, the caller's stack and return address.

| value | factor | bias | low-word result |
| --- | --- | --- | --- |
| 6 | 7 | -5 | 37 |
| -9 | 3 | 1 | -26 |
| INT64_MAX | 2 | 7 | 5 |
| INT64_MIN | -1 | 0 | INT64_MIN |

Predict all four rows before running. The negative minimum is not a representable positive signed value, so an ordinary signed multiplication by -1 is not an equivalent C implementation. The unsigned operation deliberately retains the minimum bit pattern.

## Build and check the supplied baseline

From the project folder:

```sh
cmake -S starter -B build-O0 -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_C_FLAGS_DEBUG="-O0 -g"
cmake --build build-O0
ctest --test-dir build-O0 --output-on-failure
./build-O0/assembly_compiler
cmake -S starter -B build-O2 -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_C_FLAGS_RELEASE="-O2 -g -DNDEBUG"
cmake --build build-O2
ctest --test-dir build-O2 --output-on-failure
./build-O2/assembly_compiler
```

Both supplied roles print four matching result rows and exit zero. Each contract run checks 10,013 fixed and deterministic full-width triplets plus six preserved registers; its explicit checks remain active in Release. The task remains the worksheet evidence. No intentionally broken program must be repaired in this unit.

The first output row is value=6 factor=7 bias=-5 result=37; the later results are -26, 5 and -9223372036854775808. For the reference use -S solution in separate build folders. Repeat with both compiler options set to gcc, and record each compiler's actual observations separately.

## Generate real compiler assembly

From the selected role folder:

```sh
mkdir -p observed
clang -std=c17 -O0 -g -S -masm=intel -fverbose-asm model.c -o observed/model-O0.s
clang -std=c17 -O2 -g -S -masm=intel -fverbose-asm model.c -o observed/model-O2.s
```

- -S stops compilation at assembler input, before producing an object or linking.
- -masm=intel selects Intel notation for the x86 listing.
- -fverbose-asm adds compiler-generated commentary; comments and directives are not executed instructions.
- -O0 and -O2 control the compared optimization levels. Keep every other recorded flag and input fixed.

Repeat with gcc under different observed filenames. Locate compiled_score in each actual file. Separate labels/directives/comments from instructions. Annotate argument movement, multiplication, addition, representation copying and return. At -O0, look for stack locals or additional moves; at -O2, identify any eliminated copies or combined operations. Treat these as observations, not mandatory instruction templates.

## Compare text with linked instructions

```sh
objdump -d -M intel build-O0/assembly_compiler > observed/linked-O0.txt
objdump -d -M intel build-O2/assembly_compiler > observed/linked-O2.txt
```

The .s files are assembler input. Objdump reads linked machine instructions with final symbol addresses. Addresses and directives need not match the compiler text. Compare the compiled_score symbol boundaries and executable operations. A multiply instruction can serve signed or unsigned low-word arithmetic; reconstruct the dataflow and width rather than guessing the C type from a mnemonic alone.

## Instruction-level debugger pass

```sh
gdb ./build-O0/assembly_compiler
```

At the GDB prompt:

```text
set disassembly-flavor intel
tbreak *compiled_score
run
info registers rdi rsi rdx rax rsp
disassemble compiled_score
si
finish
print $rax
continue
```

The first instruction receives 6, 7 and -5 and returns 37. The * breakpoint observes registers before the prologue can move them. Trace actual instructions through the multiply/add and representation copy. Repeat against build-O2: optimized source-line stepping may skip or combine source statements, so use si and disassembly when the source-line view is ambiguous.

## Worksheet completion and independent work

1. Record the target, compiler version, all flags and filenames in analysis.md.
2. Predict the four default results and show both boundary bit calculations.
3. Map arguments, intermediate values and the return to actual instructions/registers/stack locations in each listing.
4. Record a real optimization difference and explain why observable outputs stay equal in the checked cases.
5. Predict a new full-width triplet, add it to main.c's input table, record its output, and keep the unchanged contracts passing.
6. Capture a GDB entry/return trace and distinguish C statements, assembly text, linked instructions and observed behavior.
7. Explain why passing a sample, fewer instructions or successful compilation does not prove worksheet completion, exhaustive correctness or a timing advantage.

Independent study follows prediction, build, listing annotation, linked disassembly, changed case and trace. A guided session uses the same worksheet and examines an actual compiler difference. An optional extension can compare another compiler or a separately changed C expression after the required evidence is complete. Leave the supplied model unchanged during the primary comparison and save learner observations before opening the reference.

## References

- [GCC output-stage options](https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html)
- [GCC code-generation commentary](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html)
- [GCC x86 assembly dialect options](https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html)
- [GNU objdump](https://sourceware.org/binutils/docs/binutils/objdump.html)
- [GDB instruction stepping](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)
