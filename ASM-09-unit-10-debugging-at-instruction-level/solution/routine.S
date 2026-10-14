#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 System V."
#endif
.intel_syntax noprefix
.text
.global debug_first_nonnegative
.type debug_first_nonnegative, @function
debug_first_nonnegative:
    .cfi_startproc
    xor ecx, ecx
.Ldebug_loop:
    cmp rcx, rsi
    jge .Ldebug_missing
    mov r8d, DWORD PTR [rdi + rcx * 4]
    cmp r8d, 0
.global debug_branch_decision
debug_branch_decision:
    /* DEBUG_SIGNED_BRANCH: diagnose this decision from actual flags. */
    jge debug_found
.global debug_advance
debug_advance:
    inc rcx
    jmp .Ldebug_loop
.global debug_found
debug_found:
    mov rax, rcx
    ret
.Ldebug_missing:
    mov rax, -1
    ret
.cfi_endproc
.size debug_first_nonnegative, .-debug_first_nonnegative
.section .note.GNU-stack,"",@progbits
