#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_openat
.type lab_openat, @function
lab_openat:
    mov r10, rcx
    mov eax, 257
lab_openat_boundary:
    syscall
    ret
.size lab_openat, .-lab_openat
.section .note.GNU-stack,"",@progbits
