#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_write
.type lab_write, @function
lab_write:
    /* TODO SYSCALL_WRITE: select Linux write and enter the kernel. */
    mov rax, -38
lab_write_boundary:
    ret
.size lab_write, .-lab_write
.section .note.GNU-stack,"",@progbits
