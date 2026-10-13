# Unit 5: The Stack and Function Calls

Compose two real assembly calls while preserving the caller's state. This replaces the earlier opening leaf arithmetic exercise with a stack-frame task. The later C interop project adds a separate five-to-three argument mapping and clamp contract; this project focuses on two nested assembly calls and their stack lifetime.

## Target, files and learner task

Use Linux x86-64, System V AMD64, GNU/Clang Intel syntax, CMake 3.20 or later, Clang or GCC, GDB and objdump. Use an x86-64 Linux VM or lab on macOS, or an x86-64 WSL distribution on Windows. Each role builds independently with `routine.S`, `stack.h`, `main.c`, `tests.c`, `abi_checks.S` and `CMakeLists.txt`.

Complete only `STACK_CALLS` in `starter/routine.S`. The supplied `stack_leaf` remains unchanged. Record a stack diagram before editing. Save the learner attempt before comparing the separate reference.

## Exact two-call contract

```c
int64_t stack_leaf(int64_t input);
int64_t stack_pair(int64_t a, int64_t b);
```

Every signed 64-bit input is valid. The leaf returns the signed interpretation of the low 64 bits of `2 * input + 5`. The pair routine calls that leaf first for a and then for b, exactly once each, and adds the two returned bit patterns modulo 2^64. Thus the final result is the signed interpretation of the low 64 bits of `2*a + 2*b + 10`. C tests use unsigned arithmetic and copy the bits into `int64_t`; signed C overflow is not part of the contract.

The pair receives a in RDI and b in RSI and returns its result in RAX. Before each call to the leaf, move that call's input into RDI. The leaf may change RDI, RSI, RDX, RCX and R8 through R11. Its supplied implementation deliberately clears those caller-saved registers after computing RAX. Holding b or the first result in one of those registers across a call is incorrect.

Preserve RBX, RBP and R12 through R15, the stack pointer and return address. If a preserved register holds temporary state, save its incoming value before changing it and restore it before return. Keeping the numeric answer while skipping or substituting the two calls is incomplete: the native probe checks actual call count and ordered inputs.

## Stack lifetime and alignment

At the pair entry, RSP is 8 modulo 16 because its caller pushed an eight-byte return address. Before either nested call, RSP must be 0 modulo 16. The leaf then enters at 8 modulo 16. Both calls must observe this entry alignment.

One possible frame saves two eight-byte registers and reserves another eight bytes. The total 24-byte adjustment turns an entry remainder of 8 into a call-site remainder of 0. After both calls, undo the reservation and restore the saved registers in reverse order. Another valid frame can save three registers. Explain each push, subtraction, call, return, addition and pop with the actual address and stack remainder.

For a=3 and b=7, the first leaf returns 11 and the second returns 19. Keep b live while the first call clears RSI and keep 11 live while the second call replaces RAX. Return 30 after restoring the original frame.

| Point | RSP remainder mod 16 | Live values |
| --- | --- | --- |
| pair entry | 8 | a in RDI, b in RSI |
| after a balanced 24-byte frame | 0 | saved b, saved caller registers |
| first leaf entry | 8 | input 3; return address points into pair |
| after first leaf return | 0 | result 11 must remain live |
| second leaf entry | 8 | input 7; earlier result saved |
| after second leaf return | 0 | results 11 and 19 |
| pair return | 8 | original caller registers and return address restored |

## Build, complete and test

From the project folder:

```sh
cmake -S starter -B build-starter -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-starter
ctest --test-dir build-starter --output-on-failure
./build-starter/assembly_stack
```

The untouched starter builds, fails its contracts and exits 78 with an unfinished-task message on stderr and no successful rows. After a correct frame and two calls, the demo prints:

```text
a=3 b=7 result=30
a=-5 b=19 result=38
a=9223372036854775807 b=1 result=10
a=-9223372036854775808 b=-1 result=8
```

Build the reference with `-S solution -B build-solution`. Repeat completed learner and reference in separate Release folders. For GCC set both compiler options to `gcc`.

Each healthy profile checks 10,012 fixed and deterministic full-width pairs, six preserved registers, two actual leaf invocations, ordered arguments and both leaf-entry alignments. The instrumented test leaf runs the same arithmetic and register-clobbering instructions as the production leaf, adding only observation of its call boundary. A separate arbitrary-precision Python oracle verifies the full-width results. The ordinary demo does not link the observer globals.

## Debugger trace of the actual nested call

```sh
objdump -d -M intel build-solution/assembly_stack
gdb ./build-solution/assembly_stack
```

At the GDB prompt:

```text
set disassembly-flavor intel
tbreak *stack_leaf
run
info registers rdi rsi rax rsp
print ((unsigned long)$rsp & 15)
x/gx $rsp
finish
print $rax
continue
```

The first leaf receives 3, has an entry remainder of 8 and returns 11. Its saved return address points back into stack_pair. For a longer trace, start at stack_pair, use `si` through the frame and both calls, and record the restored RBX/R12 values and final RAX=30. Record observed addresses instead of assuming a fixed layout.

## Completion evidence and independent practice

1. Record the two-call pseudocode, register lifetime table and balanced stack diagram.
2. Complete only the pair body and pass Debug/Release with Clang/GCC.
3. Predict and record the four default rows and at least one changed full-width pair.
4. Trace both nested calls and show their ordered arguments, entry alignment, return values and final frame restoration.
5. Explain why holding b in RSI or the first result in RAX across the next call loses information, and why returning the formula without invoking the leaf misses the task.

Independent study follows prediction, frame sketch, edit, contract tests and instruction tracing. A guided walkthrough follows the same evidence and diagnoses the first failed boundary check. An optional extension can use a different balanced frame after the required contract passes; the leaf, call order and inputs remain unchanged.

## References

- [System V x86-64 ABI project](https://gitlab.com/x86-psABIs/x86-64-ABI)
- [GNU assembler Intel syntax](https://sourceware.org/binutils/docs/as/i386_002dVariations.html)
- [GDB instruction stepping](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)
