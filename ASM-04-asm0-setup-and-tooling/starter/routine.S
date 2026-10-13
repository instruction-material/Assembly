#if !defined(__linux__) || !defined(__x86_64__)
#error "This project requires the Linux x86-64 System V target."
#endif
.intel_syntax noprefix
.text
.global transform_value
.type transform_value, @function
transform_value:
    /* TODO ASM_TRANSFORM: return the low 32 bits of 2 * input + 5. */
    mov eax, edi
    ret
.size transform_value, .-transform_value
.section .note.GNU-stack,"",@progbits
