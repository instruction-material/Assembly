# Sign and zero extension into complete 64-bit values

Follow the same low bits through two interpretations. This extension lab pairs
signed widening with unsigned widening at byte, word and doubleword widths.
Keep its attempt separate from the partial-write and calculator projects.

## The source width chooses the sign bit

For an n-bit source, retain only its low n bits. Unsigned widening fills the
new high bits with zero. Signed widening uses bit n-1 to preserve that source's
two's-complement value. A source can be negative as a byte yet positive as a
word, so the full original 64-bit word does not choose the narrow sign bit.

Each stage first loads the same initial seed into RAX, then applies its full
widening instruction. The completed output is independent of that seed.
For default `initial=1122334455667788` and `incoming=11223344800080ff`:

| Output | Width instruction | Complete stored word |
| --- | --- | --- |
| byte-signed | `movsx rax, sil` | `ffffffffffffffff` |
| byte-unsigned | `movzx eax, sil` | `00000000000000ff` |
| word-signed | `movsx rax, si` | `ffffffffffff80ff` |
| word-unsigned | `movzx eax, si` | `00000000000080ff` |
| dword-signed | `movsxd rax, esi` | `ffffffff800080ff` |
| dword-unsigned | `mov eax, esi` | `00000000800080ff` |

The hexadecimal output slots occupy offsets 0, 8, 16, 24, 32 and 40. The
unsigned byte/word forms write EAX; the resulting 32-bit write also clears
RAX's upper half. The signed byte/word forms explicitly target 64-bit RAX.
MOVSXD supplies the 32-to-64 signed case. Read both source and destination
widths instead of treating the mnemonic alone as a complete description.

The C model masks the source, tests its narrow sign bit, and subtracts 2^n
when that bit is set. The intermediate calculation fits in signed 64 bits for
n equal to 8, 16 or 32. Conversion of a negative result to `uint64_t` supplies
the displayed modulo-2^64 pattern. It avoids an out-of-range cast to a narrow
signed C type; the modeled interpretation is explicit.

## Repair the selected interpretation

The named `SIGN_BYTE` learner instruction currently zero-extends the byte in
the signed-byte slot. Select the signed widening into the documented full
destination. Keep the other five forms, model, caller and checks unchanged.
The default low byte `ff` denotes -1 under signed-byte interpretation and 255
under unsigned-byte interpretation. Explain why the two stored patterns must
therefore differ even though the source bits are identical.

With `--changed`, initial is `ffeeddccbbaa0099` and incoming is
`fedcba987fff7f80`. The six rows are `ffffffffffffff80`,
`0000000000000080`, `0000000000007f80`, `0000000000007f80`,
`000000007fff7f80` and `000000007fff7f80`. The byte sign bit is set, while the
word and doubleword sign bits are clear. The high incoming bits do not alter
these selected narrow-source interpretations.

## Reject an interpretation regression in an owned copy

After acceptance, copy the role into a separate experiment folder. Replace
only the unsigned-word form with `movsx rax, si`, predict the first negative
word boundary that will distinguish it, and run the unchanged contracts.
Record the rejected case and its expected unsigned pattern. Restore the
correct role before final acceptance. A separate copied RBX-clobber experiment
must fail the ABI check even if every output word matches the model.

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
