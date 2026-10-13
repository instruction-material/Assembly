# ASM3 String Length and Copy

Walk byte strings in Linux x86-64 assembly and distinguish source length from the number of bytes stored in a destination. The learner completes the remaining-source count after truncation or a zero-capacity copy.

## Target and files

Use Linux x86-64, the System V AMD64 ABI, GNU/Clang Intel syntax, CMake 3.20 or later, Clang or GCC, and GDB. The `.S` suffix enables preprocessing. Use an x86-64 Linux VM or lab on macOS, or an x86-64 WSL distribution on Windows.

Each independent role folder contains `string_routines.S`, `string_routines.h`, `main.c`, `tests.c`, `abi_checks.S`, and `CMakeLists.txt`. Work in `starter/`; use `solution/` to review a tested attempt. The string-length and bounded-copy loops are already present. Complete the single `COPY_SOURCE_LENGTH` task in `string_routines.S` without editing the tests.

## Exact contract

```c
uint64_t asm_strlen_simple(const char *text);
uint64_t asm_strlcpy_simple(char *dest, const char *src,
                             uint64_t capacity);
```

`text` and `src` must be readable through a terminating zero byte. Length counts bytes before that byte. This is a byte-string exercise: a multi-byte character may occupy several bytes.

For the copy:

- Source and destination do not overlap.
- With `capacity > 0`, the caller supplies at least that many writable destination bytes.
- Store at most `capacity - 1` source bytes, then a zero byte. Leave the rest of the destination unchanged.
- With `capacity == 0`, never access the destination; it may be null. Still read the valid source and return its length.
- Always return the full source length, excluding the zero terminator, even when the destination stores only a prefix.
- Never modify the source or read beyond its first zero byte.
- Preserve RBX, RBP and R12 through R15, the stack pointer and return address.

The caller establishes valid source termination and destination capacity. The routine does not inspect arbitrary pointers to decide whether they are valid. A destination bound controls writes; it does not shorten the source-length result.

## Registers, widths and loop state

String length receives `text` in RDI and returns its unsigned 64-bit byte count in RAX. Copy receives destination in RDI, source in RSI and unsigned capacity in RDX; it returns the full source length in RAX. Each pointer step advances by one byte.

The existing copy loop uses RCX as its source/destination index. It stops copying when it sees a zero byte or reaches the reserved terminator position. After truncation, continue counting source bytes from the current RCX without writing more destination bytes. With zero capacity, start that count at zero. Test capacity before subtracting one, so zero does not become a very large unsigned bound.

An unsigned bound comparison expresses byte-count and capacity checks. A zero-byte test expresses source termination. Record which instruction sets the flags before each branch.

## Predict the example

The source is `assembly`, eight bytes plus its terminator:

| Destination capacity | Stored text | Returned source length |
| --- | --- | --- |
| 16 | assembly | 8 |
| 6 | assem | 8 |
| 1 | empty string | 8 |
| 0 | destination untouched | 8 |

For capacity 6, the destination holds `a s s e m` followed by a zero byte. The remaining source bytes `b l y` are still counted. With positive capacity, a returned length greater than or equal to capacity shows that the source did not fit.

## Build, complete and test

From this project folder:

```sh
cmake -S starter -B build-starter -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-starter
ctest --test-dir build-starter --output-on-failure
./build-starter/assembly_strings
```

The untouched starter builds but fails the completion contracts. Its demo exits `78`, reports the unfinished or incorrect routine on stderr, and prints no successful result rows. After completion, the same commands pass and print:

```text
strlen=9
wide length=8 text=assembly
small length=8 text=assem
zero capacity length=8
```

Build the reference with `-S solution -B build-solution`. Repeat both completed roles with `-DCMAKE_BUILD_TYPE=Release` in separate folders. For GCC, set both compiler options to `gcc`.

The tests check 35,900 source/capacity pairs per successful profile. They cover lengths 0 through 64, capacities 0 through 68, eight byte patterns including high-bit bytes, empty strings, null or inaccessible zero-capacity destinations, exact fits, truncation, unchanged destination tails, unchanged source bytes and six preserved registers for both routines. Twenty protected-memory cases put the source terminator and destination capacity beside inaccessible pages.

The protected cases catch an extra source read or destination write in those fixtures. The remaining cases compare every destination byte against the expected copy and verify that bytes outside the copy remain unchanged.

## Debug the truncated copy

```sh
gdb ./build-solution/assembly_strings
```

At the GDB prompt:

```text
set disassembly-flavor intel
tbreak asm_strlcpy_simple if $rdx == 6
run
info registers rdi rsi rdx rcx rax
x/s $rsi
set $saved_dest = (char *)$rdi
disassemble asm_strlcpy_simple
si
finish
print $rax
x/s $saved_dest
continue
```

Predict capacity 6, source length 8 and stored text `assem`. Use `si` repeatedly to trace the copy loop and remaining-source count before `finish`. Record the source index, destination write address, bound check and zero-byte test. Explain which path writes the terminator and why the count continues after destination writes stop.

## Completion evidence

1. Complete only the named task, keeping the supplied function signatures and tests.
2. Pass Debug and Release with Clang and GCC for the completed starter and reference.
3. Record the four expected demo rows and the debugger's truncated-copy result.
4. Predict and test a custom source under capacities 0, 1, an exact fit and a truncating bound.
5. Explain the difference between source length, stored byte count and available destination capacity, including the terminator.

For independent study, follow prediction, edit, test and trace in that order. In an instructor-guided session, discuss the capacity table before editing and have the learner explain the first failed assertion. An optional extension can add a separately named bounded-length routine with an explicit maximum read count and its own tests after the required contract passes.

## References

- [OpenBSD strlcpy behavior](https://man.openbsd.org/strlcpy)
- [System V x86-64 ABI project](https://gitlab.com/x86-psABIs/x86-64-ABI)
- [GNU assembler Intel syntax](https://sourceware.org/binutils/docs/as/i386_002dVariations.html)
- [GDB instruction stepping](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)
