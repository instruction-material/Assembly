#if !defined(__linux__) || !defined(__x86_64__)
#error "This project requires the Linux x86-64 System V target."
#endif
.intel_syntax noprefix
.text
.global transform_value
.type transform_value, @function
transform_value:
    /* LEA computes the result; it does not read memory. */
    lea eax, [rdi + rdi + 5]
    ret
.size transform_value, .-transform_value
.section .note.GNU-stack,"",@progbits
