# Bounded Overlap Copy Direction

## Exact owned-memory contract

`lab_operation(uint64_t initial, uint64_t incoming, LabResult *output)` receives
two unsigned values in RDI/RSI and an owned five-word output object in RDX.
The routine creates its own bounded scratch storage. No input integer is an
arbitrary pointer. All six callee-saved registers, RSP and the return address
must retain their entry values. This is a Linux x86-64 System V leaf function.

The sixteen scratch bytes initially contain 01 through 10 hexadecimal.
Source offset is `initial & 7`, destination offset is `incoming & 7`, and the
requested length is `(initial >> 3) & 15`. Clamp length to both `16-source`
and `16-destination` before copying. The required result is the same as first
preserving the entire original source span and then writing its bytes at the
destination. Bytes outside the destination span remain unchanged.

Outputs are the final first and second eight-byte little-endian words, actual
copied count, original source offset and original destination offset. Zero
length performs no byte read or write. A higher destination uses the backward
loop; other destinations use the forward loop. Backward copying is also valid
for disjoint spans. The routine uses ordinary byte loads/stores, so it never
changes the processor direction flag.

The starter chooses the opposite direction. Repair only COPY_DIRECTION to
select backward copying when destination is higher. Keep the bounds, zero
guard, loops and output stores unchanged. For the default src=1, dst=3,
count=6, forward copying overwrites source bytes before later reads. Predict
that corruption, then compare the repaired trace with preserving the original
source span. At each load/store label record offsets and owned memory.

The required Unit 7 string routine requires non-overlapping spans and counts a
zero-terminated source. This optional challenge copies a clamped byte count
with overlap; it has no string terminator contract.

In a disposable reference copy replace `ja lab_backward` with `jmp lab_forward`.
The unchanged contracts and overlapping default reject always-forward copying.

## Predict, build and explain

Default initial is `0000000000000031`, incoming `0000000000000003`. The correct five
hexadecimal outputs, in the declared order, are:

`0605040302030201 100f0e0d0c0b0a07 0000000000000006 0000000000000001 0000000000000003`

`--changed` uses zero for both inputs. This special case agrees even with the
named starter mistake and copied regression; it does not prove the general
contract. Predict another nonzero index or unequal overlapping span before
running it. The untouched starter builds but its default demo exits 78 and
unchanged contracts fail. Complete only COPY_DIRECTION in `routine.S`.

Use ordinary-user Linux x86-64, GNU Intel assembly syntax, CMake 3.20+, GCC or
Clang, GDB and binutils. On macOS use an x86-64 Linux lab or VM; on Windows use
an x86-64 WSL distribution. The site IDE edits, saves and exports these sources.
Each role includes routine.S, main.c, lab.h, model.c, tests.c, abi_checks.S,
CMakeLists.txt and trace.md. Roles differ only in routine.S. Keep this README
one level above the selected role. From that role directory:

```sh
cmake -S . -B build-Debug -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-Debug --verbose --parallel 1
./build-Debug/app
ctest --test-dir build-Debug --output-on-failure
./build-Debug/app --changed
cmake -S . -B build-Release -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-Release --verbose --parallel 1
ctest --test-dir build-Release --output-on-failure
./build-Release/app --changed
objdump -d -M intel build-Debug/app
gdb ./build-Debug/app
```

Repeat with GCC in separate build directories. Unsupported arguments exit 64.
The independent C model uses C record/pointer expressions for the table task
and memmove for the overlap task. It never calls the assembly operation. The
unchanged explicit checks remain active in Release and cover 10,269 pairs:
sixteen boundary values crossed with themselves and 10,013 deterministic
additional pairs. The separate probe checks the six preserved registers and
stack restoration. Preserve the supplied C files and ABI probe.

In GDB use `set disassembly-flavor intel`, `break lab_operation` and `run`.
Save `set $entry_sp = $rsp`, `set $return_pc = *(unsigned long long*)$rsp`
and `set $output = $rdx`. Follow the task's labeled memory operations. Record
current instruction PCs, actual addresses, valid byte ranges, access widths
and before/after values. At lab_return check the original RSP and return word,
inspect all five output words through `$output`, then step RET to verify the
caller PC and `$rsp == $entry_sp + 8`. Use current addresses for each run.

Retain the untouched failure, named repair, actual memory trace, both compiler
and build modes, a boundary prediction and the rejected copied regression in
trace.md. Code tests do not complete that explanation.

References: [System V AMD64 ABI](https://gitlab.com/x86-psABIs/x86-64-ABI/-/blob/master/x86-64-ABI/low-level-sys-info.tex),
[memmove contract](https://man7.org/linux/man-pages/man3/memmove.3.html).
