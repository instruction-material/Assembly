# Decode a Record: Addresses, Bytes and Register Widths

Assembly, Unit 1. This project reads one selected record from a supplied byte array. It makes the distinction between an address, the bytes stored there and the value produced by a load visible. It is a different task from ASM0's build-and-call setup, the later integer calculator and Unit 7's byte-walking memory routines. Follow this fixture through source, objects, symbols, relocation, linking and loading, then complete its bounded leaf function and trace. No parser, allocator or general-purpose record system is required.

## Target, files and build

Use an owned Linux x86-64 lab, CMake 3.20+, Clang or GCC, GDB and objdump. On Apple Silicon use an x86-64 Linux VM or lab; the browser and native macOS terminal do not run this System V ELF program. An ARM64 Linux machine is also a different instruction target. On Windows use an x86-64 WSL distribution. On an owned Ubuntu lab the relevant packages are build-essential, clang, cmake, gdb and binutils. Package installation belongs to that lab's administration.

Select the learner role in the site IDE, save and export its files, then extract them. Keep routine.S, record.h, main.c, tests.c, abi_checks.S, CMakeLists.txt, trace.md and this guide together with their selected role layout. The capital S tells the compiler driver to preprocess the assembly source before assembling it. The source selects GNU assembler Intel syntax, where the destination precedes the source and memory operands use brackets. This target's convention passes the first four integer/pointer arguments in RDI, RSI, RDX and RCX; the integer result returns in RAX. C supplies the driver, output object and unchanged tests.

From the extracted project's root:

```sh
cmake -S starter -B build-starter -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_C_FLAGS_DEBUG="-O0 -g" -DCMAKE_ASM_FLAGS_DEBUG="-O0 -g" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build-starter --parallel 1
ctest --test-dir build-starter --output-on-failure
./build-starter/assembly_demo
```

The supplied starter compiles but deliberately returns zero for every call. Its contracts fail and its demonstration reports an unfinished decoder with exit 78. Retain that result before editing. Change only routine.S to satisfy record.h; leave the C driver, tests and ABI checker intact. Use separate build-reference and build-gcc directories when inspecting the solution or changing compiler. Run the same CMake commands with the corresponding source directory and both compiler options set to gcc for the GCC comparison.

## Follow source through objects, linking and loading

Use the decoder as one small artifact trail. main.c is C source that calls an external function declared in record.h; routine.S defines that function. The compiler driver preprocesses and compiles the C translation unit, and preprocesses and assembles the .S translation unit. Their object files contain machine instructions, sections, symbols and any relocations still needed. CMake archives the assembly object in librecord_decode.a and links it with the caller to produce assembly_demo. An archive is a collection of objects, not an independently runnable program.

The .S file uses Intel syntax because of its explicit directive; compiler output can be requested in either syntax. Intel `mov r9d, dword ptr [r8 + 4]` and AT&T `movl 4(%r8), %r9d` describe the same destination width and memory source. Operand order and notation differ. Compare the disassembly's instruction, its actual bytes, the operand address and the loaded value as four separate observations.

Before completing the starter, inspect the Debug build it already produced:

```sh
readelf -hW -sW build-starter/CMakeFiles/record_decode.dir/routine.S.o
readelf -Wr -sW build-starter/CMakeFiles/assembly_demo.dir/main.c.o
objdump -dr -M intel build-starter/CMakeFiles/assembly_demo.dir/main.c.o
readelf -hW -lW build-starter/assembly_demo
objdump -d -M intel --disassemble=decode_record build-starter/assembly_demo
```

The assembly object is an ELF64 relocatable object, with a defined decode_record function symbol. The caller object has an undefined decode_record symbol and a relocation referring to it. Undefined at this stage describes a reference that another link input supplies. Record the actual relocation offset and type; do not copy one compiler's value into another build's table. The linked program contains the decoder definition at a resolved instruction address. Its ELF header type can be EXEC or DYN depending on the target's linking configuration. Read the program headers and interpreter along with that type; DYN alone does not distinguish every shared object from a position-independent executable or prove a hardening property.

The linker joins the caller, the selected archive member and the required runtime/library inputs. It resolves the static call's reference within this program. Dynamic runtime/library references can still require loader work. The operating system maps the executable and its segments, and the recorded interpreter participates in dynamic loading. C runtime startup eventually calls main. Runtime addresses observed in GDB can differ from the image addresses shown in a static listing, especially for a position-independent executable. Keep the artifact stage and process identity beside every address.

Use the ordinary build command's `--verbose` option to retain its actual compiler and linker invocations. A syntactically valid object can still contain an incorrect function: the untouched decoder builds and links but fails its behavior contracts. A different failure occurs if the decoder's definition is omitted at link time. The automated lab deliberately links the caller object alone to a separate temporary output and checks that the linker rejects its missing decode_record. It leaves the successful executable intact. A successful link, a successful run and a correct decoder are separate checks.

### Compare compiler settings without inventing a speed result

Build a separate Release folder after the learner contracts pass:

```sh
cmake -S starter -B build-starter-O2 -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_C_FLAGS_RELEASE="-O2 -g -DNDEBUG" -DCMAKE_ASM_FLAGS_RELEASE="-O2 -g -DNDEBUG" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build-starter-O2 --verbose --parallel 1
ctest --test-dir build-starter-O2 --output-on-failure
./build-starter-O2/assembly_demo
./build-starter-O2/assembly_demo --changed
objdump -dr -M intel --disassemble=main build-starter/CMakeFiles/assembly_demo.dir/main.c.o
objdump -dr -M intel --disassemble=main build-starter-O2/CMakeFiles/assembly_demo.dir/main.c.o
```

The Debug commands above explicitly select -O0 and the Release commands explicitly select -O2. Their compile_commands.json files record the invocations for each source file. Compare the actual C caller bodies, not whole text dumps that differ merely because a filename changed. The compiler can change the caller's layout and instruction choices while preserving its observed behavior. Record changes or unchanged structure without assuming that optimization always makes every function shorter.

The handwritten decoder has no optimization-dependent source branch. The native lab extracts its actual .text section and compares Debug with Release within each role and compiler. Passing -O2 to the assembly driver does not turn that handwritten function into optimized C. Changes in its C caller and unchanged decoder instructions therefore illustrate different parts of the pipeline. Debug information, whole object hashes and absolute addresses can differ even when these decoder instruction bytes match.

Record Clang/GCC, CMake and binutils versions, flags, object and executable identities, caller reference, relocation, resolved decoder and actual output in trace.md. Repeat the comparison with GCC using a separate build folder. Do not compare elapsed time from these runs as a performance experiment. Unit 9 studies C-to-instruction mapping and optimizer transformations in more depth; Unit 11 adds controlled repeated timing. Here the completion evidence is the complete source/object/link/load trail, preserved behavior and a justified instruction trace.

## Read the byte-level contract

A record occupies eight consecutive bytes. Offsets 0 and 1 encode a signed 16-bit delta; offsets 2 and 3 encode an unsigned 16-bit size; offsets 4 through 7 encode an unsigned 32-bit tag. Values are little-endian: the least significant byte comes first. RecordView is a separate, writable 32-byte output object with four eight-byte fields: the selected record address, delta, size and tag. Header assertions fix their offsets at 0, 8, 16 and 24. The byte array is not reinterpreted as a naturally aligned C structure.

The caller provides count readable records and a distinct output object. For a non-null base and output and an index below count, return one and fill all fields. Compute the selected address as base + index * 8. The index and count are unsigned sizes; an unsigned comparison rejects index equal to count and very large indices. When either pointer is null or the index is out of range, return zero without reading a record or changing the output. These checks do not validate every arbitrary non-null pointer. The caller still supplies actual readable/writable storage, nonoverlap and a representable count * 8.

An effective-address instruction such as LEA calculates an address. It does not fetch the record's contents. A memory load at that address reads bytes. A sign-extending 16-bit load makes the delta's upper bits match bit 15; a zero-extending load makes the unsigned size's upper bits zero. In this 64-bit mode, writing a 32-bit general-purpose destination also clears that register's upper 32 bits. Loading the tag through a 32-bit destination therefore preserves tags above 2,147,483,647 as positive 64-bit values. A 16-bit register write alone does not perform that clearing.

For the first default record, bytes 00 80 encode delta -32768, ff ff encode size 65535, and 00 00 00 80 encode tag 2147483648. The next record's ff ff delta is -1 while its ff ff ff ff tag is 4294967295. The same high bits require different extensions because their declared widths and interpretations differ. Predict every row in trace.md before consulting output. The demonstration prints actual addresses from this process; those addresses are observations rather than fixed answer values.

## Trace the completed function

After the unchanged contracts pass, use the Debug learner build:

```sh
objdump -d -M intel build-starter/assembly_demo
gdb -q build-starter/assembly_demo
```

Inside GDB, use `set disassembly-flavor intel`, `break decode_record`, `run`, `info registers rdi rsi rdx rcx`, `x/8bx $rdi` and `display/i $pc`. Use `si` to advance individual instructions, observing registers and output memory between them. Record the selected address before the first load and the register after each load. Continue through the return and compare the C output. Repeat at a nonzero index so the stride calculation is visible. Instruction addresses and data addresses serve different purposes; label both.

Run `./build-starter/assembly_demo --changed` and repeat the byte predictions. The changed table preserves the eight-byte format but changes signed fields, unsigned fields and high-bit tags. Keep that run's own addresses and bytes. Compare the same record's predicted and observed fields, explain each extension and name an observation that would contradict the explanation. A separate run can place the same data at a different address because of process layout and address randomization. Equality of values does not establish equality of addresses across processes.

The native contracts exercise all 65,536 delta bit patterns at three indices on a deliberately unaligned base, independent C byte decoding, unchanged source bytes, invalid-call output preservation, six callee-saved registers and a record immediately before an inaccessible guard page. Index one with count one must be rejected before accessing that next page. These contracts do not make arbitrary pointers safe or establish behavior on another architecture. Debug and Release, both compilers, and an actual debugger trace supply different checks.

Finish trace.md after code passes. Preserve the original failure, build commands, actual byte/register trace, changed case and limits. The reference is a separate role; compare only after a working attempt. Independent reading follows the same prediction, single-step and explanation sequence that a paced walkthrough pauses through with an instructor. Passing code alone does not complete the explanation.

For syntax detail see the [GNU assembler syntax guide](https://sourceware.org/binutils/docs/as/i386_002dVariations.html) and [memory-reference guide](https://sourceware.org/binutils/docs/as/i386_002dMemory.html). The [x86-64 psABI project](https://gitlab.com/x86-psABIs/x86-64-ABI) maintains the target calling convention.

Artifact and compiler references: [GNU readelf](https://sourceware.org/binutils/docs/binutils/readelf.html), [CMake compile commands](https://cmake.org/cmake/help/latest/variable/CMAKE_EXPORT_COMPILE_COMMANDS.html), and [GCC optimization options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html).
