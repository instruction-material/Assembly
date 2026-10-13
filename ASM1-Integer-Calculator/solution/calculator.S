#if !defined(__linux__) || !defined(__x86_64__)
#error "Use the Linux x86-64 System V target."
#endif
.intel_syntax noprefix
.text
.global asm_eval_expression
.type asm_eval_expression, @function
asm_eval_expression:
    cmp dl, '+'
    je .Ladd
    cmp dl, '-'
    je .Lsub
    cmp dl, '*'
    je .Lmul
    cmp dl, '/'
    je .Ldiv
    cmp dl, '&'
    je .Land
    cmp dl, '^'
    je .Lxor
    jmp .Lunsupported
.Ladd:
    mov rax, rdi
    add rax, rsi
    ret
.Lsub:
    mov rax, rdi
    sub rax, rsi
    ret
.Lmul:
    mov rax, rdi
    imul rax, rsi
    ret
.Ldiv:
    test rsi, rsi
    je .Lunsupported
    cmp rsi, -1
    jne .Ldivide_valid
    mov rax, 0x8000000000000000
    cmp rdi, rax
    je .Lunsupported
.Ldivide_valid:
    mov rax, rdi
    cqo
    idiv rsi
    ret
.Land:
    mov rax, rdi
    and rax, rsi
    ret
.Lxor:
    mov rax, rdi
    xor rax, rsi
    ret
.Lunsupported:
    /* Outside the valid-expression contract, return zero defensively.
     * The checked caller rejects these inputs before invoking assembly. */
    xor eax, eax
    ret
.size asm_eval_expression, .-asm_eval_expression
.section .note.GNU-stack,"",@progbits
