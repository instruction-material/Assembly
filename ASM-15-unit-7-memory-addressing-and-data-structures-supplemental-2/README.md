# Pointer Table Lookup and Record Fields

## Exact owned-memory contract

`lab_operation(uint64_t initial, uint64_t incoming, LabResult *output)` receives
two unsigned values in RDI/RSI and an owned five-word output object in RDX.
The routine creates its own bounded scratch storage. No input integer is an
arbitrary pointer. All six callee-saved registers, RSP and the return address
must retain their entry values. This is a Linux x86-64 System V leaf function.

The scratch frame contains four `LabRecord` objects followed by four pointers.
Each record is sixteen bytes: counter at offset 0 (eight bytes), tag at 8 (two),
state at 10 (one), reserved at 11 (one) and weight at 12 (four). The C header
asserts this exact layout. Record i has counter incoming+i, tag the low sixteen
bits of incoming XOR i*1111 hexadecimal, state i, reserved a5 and weight the low
32 bits of (incoming>>16) XOR i*01010101 hexadecimal.

The pointer table is a rotated order of the records: slot i stores the address
of record `(i + (incoming & 3)) & 3`. Select slot `initial & 3`. Outputs are
that table index, the selected record's state/index, weight, tag and its byte
offset from the start of the record array. A slot advances by eight bytes; a
record advances by sixteen. Loading a pointer from a slot and loading a field
through that pointer are separate operations.

The starter always loads slot zero. Repair only POINTER_LOOKUP so the masked
index scales by eight in the table address. Preserve the table construction,
record contents, field widths and 96-byte frame. At lab_lookup predict the slot
address and stored pointer; at lab_selected inspect the selected record and
its tag/state/weight with their actual widths. Compare a nonzero table index.

The Unit 1 required decoder follows a flat packed byte format through source,
objects and loading. This optional Unit 7 task follows an actual pointer table
and a pinned C structure layout; it does not repeat that artifact trail.

In a disposable reference copy change `movzx r9d, WORD PTR [r8 + 8]` to
`movzx r9d, BYTE PTR [r8 + 8]`. The address remains valid but the tag loses its
upper byte. The default and unchanged contracts reject this width regression.

## Predict, build and explain

Default initial is `010203040506070a`, incoming `8123456789abcdef`. The correct five
hexadecimal outputs, in the declared order, are:

`0000000000000002 0000000000000001 00000000446688aa 000000000000dcfe 0000000000000010`

`--changed` uses zero for both inputs. This special case agrees even with the
named starter mistake and copied regression; it does not prove the general
contract. Predict another nonzero index or unequal overlapping span before
running it. The untouched starter builds but its default demo exits 78 and
unchanged contracts fail. Complete only POINTER_LOOKUP in `routine.S`.

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
