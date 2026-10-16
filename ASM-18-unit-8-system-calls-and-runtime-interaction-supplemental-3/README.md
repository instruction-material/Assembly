# The fourth syscall argument and owned file creation

This extension follows four arguments across the C function ABI and the Linux
kernel ABI. Observe the permissions of an actual created file, compare raw
errors with libc, then explain why a returned descriptor alone does not prove
that the requested operation was performed correctly.

## Environment and files

Use ordinary-user Linux x86-64 with the System V AMD64 function ABI, GNU
assembler Intel syntax, C17, CMake 3.20+, Clang or GCC, GDB and strace. Confirm
the target with `uname -s` and `uname -m`. Windows uses an x86-64 WSL Linux
distribution; macOS uses an x86-64 Linux VM or lab.

Each role contains `routine.S`, `main.c`, `lab.h`, `tests.c`, `abi_checks.S`,
`CMakeLists.txt` and `trace.md`. Keep the files and this guide together after
export. Work in `starter` and save that attempt before opening the separate
reference. The browser is the editor and export path; Linux performs execution.

The two roles differ only in the named `SYSCALL_ARG4` task in `routine.S`.
The starter already enters the kernel with the correct syscall number, but it
deliberately clears the fourth kernel argument. Keep the supplied callers,
checks and requested permissions unchanged while completing that transfer.

## Follow the arguments across both boundaries

The wrapper's fixed four-argument interface is:

```c
long lab_openat(long directory, const char *path,
                long flags, unsigned long mode);
```

The C caller supplies those values in RDI, RSI, RDX and RCX. Linux x86-64 uses
RDI, RSI, RDX and R10 for the corresponding syscall arguments and syscall number
257 in RAX. Move the fourth value before the boundary. The boundary overwrites
RCX and R11; those are caller-saved registers. The original stack state and
RBX, RBP and R12–R15 still belong to the C function contract.

Here `path` is a readable zero-terminated name relative to the owned directory
descriptor. Flags select write access, exclusive creation and close-on-exec
behavior. Mode is used when creating a new file. Octal 0600 gives the owner read
and write bits; octal 0400 gives only the owner read bit. In decimal these are
384 and 256, so distinguish the display base from the underlying argument.

A successful raw result is a nonnegative descriptor; an error is a negative
kernel error code. This assembly wrapper does not convert errors into libc's
-1/`errno` convention. Capture the returned value and the separately stored
`errno` sentinel before another library call can change the observation.

## Own the complete experiment

The driver creates a unique `/tmp/assembly-openat-XXXXXX` directory using
`mkdtemp`, then opens that directory. All experiment paths are fixed relative
names inside it. No user-supplied external path is opened or replaced.

Within this single-threaded process, the driver temporarily selects umask 077
and restores its previous value during cleanup. The shell's mask is a separate
process state. On the ordinary local lab filesystem, the requested owner bits
remain while group/other bits are masked. Default filesystem ACLs can also
affect permission creation; use the documented plain local lab environment
when reproducing these exact mode comparisons.

The actual calls proceed as follows:

1. Create `owned-note` with `O_CREAT|O_EXCL` and requested mode 0600.
2. Inspect the opened descriptor with `fstat` and compare actual mode bits.
3. Try exclusive creation of the same name and observe `-EEXIST`.
4. Open `missing/note` without creation and observe `-ENOENT`.
5. Compare the existing-name failure with libc `openat`, which returns -1 and
   sets `errno` to `EEXIST`.
6. Close owned descriptors, unlink the owned note, restore the process mask,
   and remove the temporary directory on both the success and failure paths.

The untouched starter can create a file and return a descriptor. Its supplied
fourth argument is zero, so `fstat` reports mode 0000 rather than 0600. The
driver records that mismatch, cleans up and exits 78. An already opened
descriptor can remain usable even when pathname permission bits are zero;
observe the metadata rather than treating the descriptor as proof of correct
permissions. Do not add a later chmod to hide the argument error.

After completion, the first row is:

```text
raw-create mode=0600 requested=0600 errno=123
```

The error row prints target-defined numeric values for raw `EEXIST` and `ENOENT`
alongside libc's -1 and positive `EEXIST`. Raw calls preserve the sentinel 123.
`--changed` requests 0400 instead and must report that actual mode. Descriptor
numbers, directory suffixes and instruction addresses vary between runs.

## Build and verify the selected role

From the extracted project directory:

```sh
cmake -S starter -B build-first -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-first --parallel 1
ctest --test-dir build-first --output-on-failure
./build-first/app
```

Keep the untouched failure. Complete only the fourth-argument transfer, then
configure a fresh `build-completed` directory. Require CTest, `app` and
`app --changed` to succeed. Build `solution` separately. Repeat completed roles
in Release and with both compiler options set to `gcc`, using separate build
folders. The checks remain active without C assertions in Release builds.

The contract program creates three actual files in turn with requested modes
0400, 0600 and 0700, verifies all three metadata results, checks three existing
name errors plus missing-parent and invalid-descriptor errors, and checks six
preserved registers. It unlinks each created file before the next case.

## Inspect the actual instruction and kernel operation

```sh
objdump -d -Mintel --disassemble=lab_openat build-completed/app
strace -f -yy -s 256 -e trace=openat,mkdir,rmdir,fstat,newfstatat,close,unlinkat,umask -o observed-openat.strace ./build-completed/app
gdb ./build-completed/app
```

Use a fresh trace filename for a changed or regression run. Separate the C
runtime's library-loading opens from the experiment's `owned-note` and
`missing/note` operations. Strace renders kernel errors using symbolic error
notation; compare that presentation with the raw return recorded by the caller.

In GDB:

```text
set disassembly-flavor intel
break *lab_openat_boundary
run
info registers rax rdi rsi rdx rcx r10 r11 rsp
x/s $rsi
x/i $rip
si
print $rax
finish
continue
```

At the first completed boundary, predict RAX=257 and R10=384. The pathname is
`owned-note`; RDI is this run's directory descriptor. Record the actual flags
and fourth argument before the instruction, then the returned descriptor and
the caller's independent metadata observation. Compare the starter's R10=0
with the completed value. The supplied ABI checker is an observer, not a file
creation workaround or a learner task.

## Completion and explanation

Complete `trace.md` with the original wrong mode, the corrected mode, the 0400
changed case, both raw errors and the libc comparison. Explain the two register
tables, the role of the process mask, exclusive creation and the full cleanup
sequence. A copied regression that clears R10 again must reproduce the wrong
mode and fail unchanged checks. Restoring the argument transfer must restore
both the contracts and the demo.

Independent study follows prediction, edit, execution and explanation. A guided
walkthrough pauses at the boundary and asks for the metadata prediction before
continuing. Passing runtime checks does not complete the written trace.

## Primary references

- [Linux syscall argument registers](https://man7.org/linux/man-pages/man2/syscall.2.html)
- [Linux open/openat creation, flags and permissions](https://man7.org/linux/man-pages/man2/open.2.html)
- [Linux v6.12 x86-64 syscall table](https://github.com/torvalds/linux/blob/v6.12/arch/x86/entry/syscalls/syscall_64.tbl)
- [glibc x86-64 fourth-argument transfer and error conversion](https://github.com/bminor/glibc/blob/glibc-2.40/sysdeps/unix/sysv/linux/x86_64/sysdep.h)
