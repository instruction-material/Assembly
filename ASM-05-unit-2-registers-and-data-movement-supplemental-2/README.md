# Partial-register writes with retained upper bits

Follow one incoming bit pattern through four destination widths. This transfer
lab makes the selected register view visible in stored 64-bit observations.
The integer-calculator project keeps its separate arithmetic and command
interface; this investigation isolates data movement and operand width.

## Predict four snapshots from two input words

Each stage reloads the original `initial` word into RAX, applies one move from
the corresponding view of RSI, and stores the complete resulting RAX. The
stages are independent snapshots, rather than a cumulative sequence.

A byte destination replaces the low eight bits and retains the other 56.
A word destination replaces the low 16 and retains the other 48. Writing EAX
produces a 32-bit value whose upper 32 RAX bits are cleared. A full RAX move
copies all 64 incoming bits. Label the selected destination on every row.

For `initial=1122334455667788` and `incoming=aabbccddeeff80ff`, predict:

| Output | Width instruction | Complete stored word |
| --- | --- | --- |
| byte | `mov al, sil` | `11223344556677ff` |
| word | `mov ax, si` | `11223344556680ff` |
| dword | `mov eax, esi` | `00000000eeff80ff` |
| qword | `mov rax, rsi` | `aabbccddeeff80ff` |

All words in these tables are hexadecimal. The output object uses offsets 0,
8, 16 and 24 in that order. The stores have eight-byte width so the retained
or cleared high bits are observable. SIL is RSI's low byte and SI its low word;
the source/destination spelling is part of the instruction contract.

The independent C model retains the original high bits with an unsigned mask
for the byte/word rows, masks the incoming low 32 bits for dword, and copies
the complete incoming word for qword. Read the masks in `model.c` and explain
which bits each retains before comparing them with an instruction listing.

## Find the first data-loss instruction

The named `WIDTH_SEED` learner task incorrectly loads the initial word through
EAX before the byte row. Its low-byte move cannot recover upper bits that an
earlier instruction already cleared. Correct the seed load's width while
keeping all four subsequent width/store pairs and the C checks intact.

The completed default demo begins with the two input words, then prints
`byte=11223344556677ff`, `word=11223344556680ff`,
`dword=00000000eeff80ff` and `qword=aabbccddeeff80ff`, one per line.
Use a full-width initial word when reproducing the first failure: an initial
value whose high 32 bits are already zero can conceal this particular bug.

With `--changed`, initial is `ffeeddccbbaa0099` and incoming is
`123456788000807f`. The byte, word, dword and qword rows become
`ffeeddccbbaa007f`, `ffeeddccbbaa807f`, `000000008000807f` and
`123456788000807f`. Explain both the retained high byte/word portions and the
cleared dword portion. These are data patterns, not signed-overflow claims.

## Reject a width regression in an owned copy

After the repaired learner passes, copy the role into a separate experiment
folder. Change only the dword-stage destination/source from EAX/ESI to AX/SI.
Predict which high bits now survive and why that contradicts its output slot.
The unchanged contracts must reject that copy. Restore the correct version
before final acceptance. A separate copied RBX-clobber experiment must also
fail the ABI check even when output values would otherwise match.

## Environment and complete files

Use an ordinary-user Linux x86-64 environment, the System V AMD64 ABI,
GNU Intel assembly syntax, C17, CMake 3.20+, Clang or GCC, GDB and binutils.
Check `uname -s` and `uname -m` before execution. Windows uses an x86-64 WSL
Linux distribution; macOS uses an x86-64 Linux VM or lab. The browser edits,
saves and exports source; Linux runs these programs.

Each role contains `routine.S`, `main.c`, `lab.h`, `model.c`, `tests.c`,
`abi_checks.S`, `CMakeLists.txt` and `trace.md`. Keep the role and this shared
guide together. Work in `starter` and save it before opening the separate
reference. The two roles differ only in the named task in `routine.S`.

The public interface is `void lab_operation(uint64_t initial, uint64_t incoming,
LabResult *output)`. The supplied C caller passes initial in RDI, incoming in
RSI and a valid output address in RDX. `LabResult` is a contiguous array of
eight-byte words, with its field count declared in `lab.h`. The caller owns
the complete writable object. This function's contract requires that object;
an arbitrary non-null address does not establish valid storage.

The routine may use RAX as working storage and must retain RBX, RBP, R12–R15,
the stack and return address. The supplied ABI probe seeds and checks those
six registers around the actual assembly call, then restores its caller's
state. Leave the probe, model, driver and contracts unchanged while repairing
the named assembly instruction and recording the separate worksheet.

## Build, observe the first failure, then compare

From the selected role folder after extracting the ZIP:

```sh
cmake -S . -B build-Debug -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-Debug --verbose --parallel 1
./build-Debug/app
ctest --test-dir build-Debug --output-on-failure
```

The untouched learner builds and links, but its default demo writes an
incomplete-width diagnostic to stderr and exits 78. The contracts exit 1.
Retain those observations before the correction. After completing only the
named instruction, rerun the demo, contracts and `./build-Debug/app --changed`.
The completed default and changed demos print the rows described above and
exit zero. An unsupported argument prints a short usage hint and exits 64.

Repeat in a fresh Release directory:

```sh
cmake -S . -B build-Release -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-Release --verbose --parallel 1
ctest --test-dir build-Release --output-on-failure
./build-Release/app --changed
```

Repeat Debug and Release with GCC by selecting `gcc` for both compilers and
using separate build directories. Checks use explicit comparisons, so Release
does not remove them. The unchanged contracts compare 256 fixed input pairs
plus 10,013 deterministic pairs with the independent unsigned-mask C model.
Every case checks the complete output and all six preserved registers.
A successful contract prints `10269 independent width cases` and its field
count. This code result still leaves the trace explanation to complete.

## Inspect current instructions and retain the evidence

```sh
objdump -d -M intel --disassemble=lab_operation build-Debug/app
readelf -Ws build-Debug/CMakeFiles/app.dir/routine.S.o
gdb ./build-Debug/app
```

In GDB use `set disassembly-flavor intel`, `break lab_operation`, `run`,
`info registers rdi rsi rdx rax rip`, and `x/i $pc`. Step the seed load with
`si`, record the resulting RAX, then step the width instruction and its store.
The public `lab_stage0`, `lab_stage1` and later labels mark the width
instructions. Set a breakpoint at each label to repeat the before/after
observation, using `x/gx` at the appropriate output address after its store.
Record the actual instruction address and current target; addresses vary.

Compare the original failing program with its corrected version for the same
default input. Locate the first incorrect transition, explain the minimal repair, and
show which unchanged assertion now holds. Repeat the table for `--changed` and
one chosen boundary pair from `tests.c`. The function reports register data;
the arithmetic/flags investigation in Unit 3 supplies the later flag contract.

Completion evidence includes both compiler/build profiles, both demos,
unchanged contracts, an annotated single-step table, and the rejected copied
regression described below. Preserve each learner/reference attempt and export
its saved `routine.S` and `trace.md` together.

## Architecture references

[Intel's Software Developer Manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
provide the architecture and instruction definitions. See Volume 1 section
3.4.1.1 for general-purpose register views, and the Volume 2B entries for
MOVSX/MOVSXD and MOVZX. The worked inputs, models, checks and trace task here
belong to this lab; use the manual to check the specific operand form.
