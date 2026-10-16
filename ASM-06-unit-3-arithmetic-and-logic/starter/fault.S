#if !defined(__linux__) || !defined(__x86_64__)
#error "Linux x86-64 System V target required"
#endif
.intel_syntax noprefix
.text
.global unguarded_divide
.type unguarded_divide,@function
unguarded_divide:
    mov rax, rdi
    cqo
.global arithmetic_fault_step
arithmetic_fault_step:
    idiv rsi
    ret
.size unguarded_divide,.-unguarded_divide
.section .note.GNU-stack,"",@progbits
