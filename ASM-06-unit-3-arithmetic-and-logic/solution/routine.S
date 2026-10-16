#if !defined(__linux__) || !defined(__x86_64__)
#error "Linux x86-64 System V target required"
#endif
.intel_syntax noprefix
.text
.global arithmetic_eval
.type arithmetic_eval, @function
arithmetic_eval:
    test rcx, rcx
    jz .Lreject
    cmp edi, 8
    ja .Lreject
    mov r11, rcx
    mov r8, rdx
    mov rax, rsi
    cmp edi, 0
    je .Ladd
    cmp edi, 1
    je .Lsub
    cmp edi, 2
    je .Lmul
    cmp edi, 3
    je .Ldiv
    cmp edi, 4
    je .Land
    cmp edi, 5
    je .Lor
    cmp edi, 6
    je .Lxor
    cmp edi, 7
    je .Ltest
    cmp rax, r8
    jmp .Lcapture_all
.Ladd:
.global arithmetic_add_step
arithmetic_add_step:
    add rax, r8
    jmp .Lcapture_all
.Lsub:
    sub rax, r8
    jmp .Lcapture_all
.Lmul:
    /* ARITH_MUL_BEGIN: complete signed one-operand multiplication. */
.global arithmetic_multiply_step
arithmetic_multiply_step:
    imul r8
    /* ARITH_MUL_END */
    pushfq
    pop r9
    and r9d, 2049
    mov r10d, 2049
    jmp .Lstore
.Ldiv:
    test r8, r8
    jz .Lreject
    mov r10, 0x8000000000000000
    cmp rax, r10
    jne .Ldivision_ready
    cmp r8, -1
    je .Lreject
.Ldivision_ready:
    /* ARITH_DIV_BEGIN: prepare the implicit dividend and divide. */
    cqo
.global arithmetic_divide_step
arithmetic_divide_step:
    idiv r8
    /* ARITH_DIV_END */
    mov r9d, 0
    mov r10d, 0
    jmp .Lstore
.Land:
    and rax, r8
    jmp .Lcapture_all
.Lor:
    or rax, r8
    jmp .Lcapture_all
.Lxor:
    xor rax, r8
    jmp .Lcapture_all
.Ltest:
    test rax, r8
.Lcapture_all:
    pushfq
    pop r9
    and r9d, 2241
    mov r10d, 2241
    mov edx, 0
.Lstore:
    mov [r11], rax
    mov [r11 + 8], rdx
    mov [r11 + 16], r9
    mov [r11 + 24], r10
    mov eax, 1
    ret
.Lreject:
    xor eax, eax
    ret
.size arithmetic_eval, .-arithmetic_eval
.section .note.GNU-stack,"",@progbits
