#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_openat
.type lab_openat, @function
lab_openat:
    /* TODO SYSCALL_ARG4: move the C fourth argument into the kernel register. */
    xor r10d, r10d
    mov eax, 257
lab_openat_boundary:
    syscall
    ret
.size lab_openat, .-lab_openat
.section .note.GNU-stack,"",@progbits
