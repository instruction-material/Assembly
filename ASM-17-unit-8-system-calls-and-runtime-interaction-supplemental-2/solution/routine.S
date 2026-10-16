#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_write
.type lab_write, @function
lab_write:
    mov eax, 1
lab_write_boundary:
    syscall
    ret
.size lab_write, .-lab_write
.section .note.GNU-stack,"",@progbits
