# Binary Hardening Evidence Lab

Compare the same bounded checksum in C and handwritten x86-64 assembly across three explicit build profiles. The program already works in both folders. The required work is prediction, binary inspection and an evidence-based explanation in `analysis.md`; `trace.md` is the separate optional runtime investigation. The reference supplies reasoning, not universal instruction addresses.

## Target and exact contract

Use Linux x86-64, the System V AMD64 ABI, CMake 3.20+, Clang or GCC, GNU objdump/readelf/objcopy and GDB. On macOS use an x86-64 Linux lab or VM; on Windows use x86-64 WSL. These are ELF/glibc observations, not a claim about Mach-O, ARM64 or every TLS guard layout.

Both functions accept a byte pointer and signed 64-bit count in RDI/RSI and return a 64-bit result in RAX. A count outside 1..32 returns zero without accessing the pointer, including a null pointer. For a valid count the pointer must address that many readable bytes. Initialize an unsigned 64-bit value to 5381; for each byte in order replace it with `value * 33 + byte`, keeping the low 64 bits. Read exactly the requested bytes, write none, and preserve RBX, RBP, R12..R15, RSP and the return address. This is a teaching checksum, not a cryptographic integrity check.

The C implementation copies the bytes into a bounded volatile local array. Volatile retains those accesses at both optimization levels; it does not make the operation atomic or thread-safe. The assembly is a leaf loop that never creates a local buffer. No buffer overflow or malformed external binary is needed for this experiment.

The demo uses the eight bytes of `Assembly` by default. An optional single argument supplies at most 32 bytes; an empty argument has count zero and returns zero. Arguments are counted as bytes, excluding the terminating NUL, rather than user-perceived characters. More than one argument or more than 32 bytes exits 2 with usage on stderr and no result row. Valid runs print count, both results and `match=yes`; a disagreement exits 1.

## Controlled build matrix

| Profile | C compilation | Executable link | Observation to investigate |
| --- | --- | --- | --- |
| baseline | -fno-stack-protector -fno-pie | -no-pie | Unprotected C, ELF EXEC |
| guard | -fstack-protector-all -fno-pie | -no-pie | C guard instrumentation, ELF EXEC |
| guard-pie | -fstack-protector-all -fPIE | -pie | C guard instrumentation, ELF DYN/PIE |

The default is `guard-pie`. These explicit profiles isolate stack guarding from position independence; they are experimental controls, not production flag recommendations. The same handwritten instructions are assembled for every profile. A C compiler's stack-protector option does not add a guard to handwritten assembly. ELF DYN is interpreted here together with the executable build/link command; an arbitrary DYN file could instead be a shared library.

From this project folder, build each profile in a separate directory:

```sh
cmake -S starter -B build-baseline -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_BUILD_TYPE=Debug -DLAB_PROFILE=baseline
cmake --build build-baseline
ctest --test-dir build-baseline --output-on-failure
./build-baseline/assembly_hardening
cmake -S starter -B build-guard -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_BUILD_TYPE=Debug -DLAB_PROFILE=guard
cmake --build build-guard
ctest --test-dir build-guard --output-on-failure
cmake -S starter -B build-guard-pie -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_BUILD_TYPE=Debug -DLAB_PROFILE=guard-pie
cmake --build build-guard-pie
ctest --test-dir build-guard-pie --output-on-failure
./build-guard-pie/assembly_hardening ABC
./build-guard-pie/assembly_hardening ""
```

Repeat with both compiler options set to `gcc`, then with Release in separate directories. The reference uses `-S solution` with its own build directories. Do not change the supplied code or tests to manufacture a pattern. Record compiler version, full configure command and actual optimization flags; source line counts do not establish instruction or timing costs.

## Static evidence and required analysis

```sh
readelf -h build-baseline/assembly_hardening
readelf -h build-guard-pie/assembly_hardening
objdump -d -M intel --disassemble=checksum_c build-guard/assembly_hardening
objdump -d -M intel --disassemble=checksum_asm build-guard/assembly_hardening
```

Repeat the disassemblies for all profiles. In the guarded C function, identify the actual guard load, saved guard, comparison/check path and possible `__stack_chk_fail` call. The Linux x86-64 glibc toolchains used for validation normally access a TLS guard through FS; record the observed operand rather than assuming an offset is universal. Compare baseline to guard first, then guard to guard-pie. Inspect the leaf assembly independently and explain its lack of automatic guard instructions.

Complete `analysis.md` with a prediction table, exact commands, function-scoped disassembly excerpts, ELF types, unchanged result checks and limits of each conclusion. CTest verifies the checksum and ABI, not worksheet completion or overall software security. A stack guard is not a per-access bounds check and does not establish pointer validity. PIE permits relocation; its ELF type alone does not prove that ASLR is enabled or that an address must change on every run. A clean checksum run cannot prove absence of unrelated bugs.

## Optional runtime trace

Complete `trace.md` after the static comparison. Use GDB on a baseline and a guarded PIE executable, break at both checksum entries, confirm the argument count, step through real instructions and record the two return values. Keep ASLR policy unchanged; `set disable-randomization off` leaves the executable's normal randomization behavior unchanged. Record the host policy, debugger setting, warnings and restrictions; the setting alone does not establish whether ASLR is enabled. Actual addresses vary with build and runtime, and equal addresses in two observations are not by themselves a test of system-wide ASLR.

```text
set pagination off
set disassembly-flavor intel
set disable-randomization off
show disable-randomization
tbreak *checksum_c
run
info registers rdi rsi rip rsp
disassemble checksum_c
si
finish
print /x $rax
tbreak *checksum_asm
continue
info registers rdi rsi rip rsp
disassemble checksum_asm
si
finish
print /x $rax
continue
```

## Completion and guided use

Independent work follows predict, build, test, inspect, compare and explain. A guided session pauses before each observed profile to predict which evidence should change. Complete the static evidence before the distinct optional runtime trace. Preserve the first worksheet before consulting the reference. All builds should pass the same 69 physical/fixed cases, including read-only page boundaries and invalid-count null pointers. Native validation additionally uses 10,010 fixed and deterministic cases from an independent arbitrary-precision Python model, six preserved registers per function and controlled regressions. These cases do not exhaust every possible 32-byte input.

## References

- [GCC stack-protector instrumentation](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)
- [GCC position-independent code generation](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html)
- [GCC executable link options](https://gcc.gnu.org/onlinedocs/gcc/Link-Options.html)
- [GNU objdump options](https://sourceware.org/binutils/docs/binutils/objdump.html)
- [GDB instruction stepping](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)
