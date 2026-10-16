# Raw Linux writes, errors and partial progress

This investigation connects a C function call to an actual Linux kernel write.
Predict the argument registers, observe the transferred bytes, compare the raw
error return with libc, then follow partial progress through an owned pipe.
The separate parser project remains the exercise for argument grammar and range.

## Target and complete role folders

Use Linux x86-64, the System V AMD64 function ABI, the Linux x86-64 syscall ABI,
GNU assembler Intel syntax, C17, CMake 3.20+, Clang or GCC, GDB and strace. Confirm
`uname -s` and `uname -m` before building. Windows uses an x86-64 WSL Linux
distribution; macOS uses an x86-64 Linux VM or lab. No administrator account is
needed for these programs.

Each role contains `routine.S`, `main.c`, `lab.h`, `tests.c`, `abi_checks.S`,
`CMakeLists.txt` and `trace.md`. Keep the selected role and this guide together.
Work in `starter`; save that attempt before opening the separate `solution`.
The browser edits, saves and exports the files. Build and run them in Linux.

The two roles differ only in `routine.S`. Complete the named `SYSCALL_WRITE`
task and the explanatory worksheet. Keep the C callers and checks unchanged.
The untouched routine returns a synthetic `-ENOSYS` value without making a
write syscall. The demo recognizes the missing behavior and exits 78 after
closing its own descriptors. Its contracts fail. A successful compilation is
therefore an initial observation, not completion.

## Two boundaries with different responsibilities

The exported C function is:

```c
long lab_write(long fd, const void *buffer, unsigned long count);
```

The caller supplies a readable buffer of at least `count` bytes and an owned
descriptor. For this three-argument function, RDI, RSI and RDX already hold the
arguments that Linux write needs. Select syscall number 1 in RAX and execute
the boundary instruction. RAX receives the result. RCX and R11 are clobbered
by that boundary; the function must still preserve RBX, RBP and R12–R15 and
return with the original stack state.

A nonnegative return counts actual bytes transferred. A negative return from
this wrapper is the raw kernel error value. This assembly function leaves C's
`errno` storage alone. In contrast, libc `write()` reports an error as -1 and
sets `errno` to its positive error code. Even libc's function named `syscall()`
performs library error conversion; it is distinct from the assembly instruction.

The same underlying failure can have different printed representations. GDB
shows the raw RAX value; strace normally formats a failed call as `-1 EBADF`.
That tracer notation does not establish that the assembly function changed
`errno`. Record the returned value and the separately captured C `errno` value.

## Predict the normal and invalid-descriptor cases

The default payload is `owned-kernel-bytes`, which has 18 bytes. The C driver
creates a pipe, sets an `errno` sentinel of 123, calls the assembly function,
then reads and compares the actual bytes. A completed first row is:

```text
raw bytes=18 errno=123 payload=owned-kernel-bytes
```

Next the driver passes descriptor -1 through both interfaces. The raw call
returns negative `EBADF` and preserves 123. The libc call returns -1 and sets
`errno` to `EBADF`. The output uses the target's numeric error values from
`errno.h`. Explain why the values are different without treating one as success.

The driver captures `errno` immediately after each call, before printing or
making another library call. Copy that observation order into the worksheet.
Changing the expected result or moving the sentinel after the call would erase
the comparison rather than implement the missing syscall.

## A successful call can transfer only part of the request

The driver next owns an empty nonblocking pipe and reads its actual capacity
with `F_GETPIPE_SZ`. This bounded fixture accepts capacities from 4096 through
65536 bytes and allocates a request twice that size. It initializes every byte
with a deterministic, nonconstant pattern.

For an observed capacity C, predict this sequence:

1. Request 2C bytes. The empty pipe accepts C, a positive short result.
2. Request one more byte while the pipe is full. The raw call returns `-EAGAIN`.
3. Drain C bytes and compare them with the original first segment.
4. Advance the source pointer by the actual first return, request the remaining
   C bytes, drain them and compare the complete 2C-byte observation.

The final row records requested, first, full-pipe error, remaining, total and
checked-byte counts. C comes from that run; it is not a hardcoded platform
promise. The `--changed` argument changes the small payload to
`changed-kernel-bytes` while retaining the partial-progress experiment.

Do not loop blindly after `EAGAIN`, add a negative error to the pointer, or
assume a positive result equals the requested count. The controlled driver
drains its own pipe to create progress. A general asynchronous writer would
also need a readiness and cancellation policy; this program makes no such
general-purpose claim. An unexpected return causes cleanup and a nonzero exit.

## Build, check and inspect

From the extracted project folder:

```sh
cmake -S starter -B build-first -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-first --parallel 1
ctest --test-dir build-first --output-on-failure
./build-first/app
```

Retain the untouched failures. Complete only the named assembly task, then use
a fresh `build-completed` directory with the same options. Require the contracts
and both `app` and `app --changed` to pass. Build `solution` independently in
`build-reference`. Repeat completed roles in Release and with both compiler
options set to `gcc`; use separate build folders.

The contracts use 65 different byte counts and binary payload bytes, check two
raw `EBADF` cases, preserve the `errno` sentinel and verify six callee-saved
registers through the supplied assembly checker. These checks remain active in
Release. The demo supplies the additional real short-write and full-pipe cases.

```sh
objdump -d -Mintel --disassemble=lab_write build-completed/app
strace -f -yy -s 131072 -e trace=write,read,pipe2,fcntl,close -o observed-write.strace ./build-completed/app
gdb ./build-completed/app
```

Use a fresh trace filename for each run. In GDB:

```text
set disassembly-flavor intel
break *lab_write_boundary
run
info registers rax rdi rsi rdx rcx r11 rsp
x/18cb $rsi
x/i $rip
si
print $rax
finish
continue
```

At the first completed boundary, predict RAX=1 and RDX=18; compare the observed
descriptor and payload address with the caller. After the instruction, predict
RAX=18. Step later error and partial cases separately. Addresses and descriptor
numbers depend on the run. The supplied checker restores its own saved caller
state and checks call-site alignment; it is not part of the learner task.

## Completion and review

Record the initial exit 78, completed byte row, both error interfaces, observed
capacity and every partial-progress count. Explain RCX/R11 clobbering, preserved
registers, pointer advancement and full-pipe handling. A copied regression that
selects read instead of write must fail the first operation; restoring the
correct syscall must restore both contracts and the demo. Do not change the
checks to accept a synthetic return.

Independent study follows prediction, implementation, execution and explanation.
A guided session traces the first call together, then asks for the error and
partial-progress predictions before running them. Passing code checks does not
complete `trace.md`.

## Primary references

- [Linux syscall ABI and the libc syscall function](https://man7.org/linux/man-pages/man2/syscall.2.html)
- [Linux write semantics](https://man7.org/linux/man-pages/man2/write.2.html)
- [Linux pipes and nonblocking writes](https://man7.org/linux/man-pages/man7/pipe.7.html)
- [Pipe capacity queries](https://man7.org/linux/man-pages/man2/F_GETPIPE_SZ.2const.html)
- [Linux v6.12 x86-64 syscall table](https://github.com/torvalds/linux/blob/v6.12/arch/x86/entry/syscalls/syscall_64.tbl)
- [glibc x86-64 syscall and error conversion implementation](https://github.com/bminor/glibc/blob/glibc-2.40/sysdeps/unix/sysv/linux/x86_64/sysdep.h)
