#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 System V."
#endif
.intel_syntax noprefix
.text
.global stack_pair
.type stack_pair, @function
stack_pair:
    /* TODO STACK_CALLS: call stack_leaf for a, then b; keep b and the first
       result across calls, align the call sites and restore all saved state. */
    xor eax, eax
    ret
.size stack_pair, .-stack_pair
.global stack_leaf
.type stack_leaf, @function
stack_leaf:
#ifdef STACK_TEST_PROBE
    mov r10, QWORD PTR [rip + stack_call_count]
    cmp r10, 2
    jae .Ltoo_many
    lea r11, [rip + stack_arguments]
    mov QWORD PTR [r11 + r10 * 8], rdi
    jmp .Lcount_call
.Ltoo_many:
    mov DWORD PTR [rip + stack_excess_calls], 1
.Lcount_call:
    inc QWORD PTR [rip + stack_call_count]
    mov r11, rsp
    and r11d, 15
    cmp r11d, 8
    je .Lalignment_ok
    mov DWORD PTR [rip + stack_alignment_bad], 1
.Lalignment_ok:
#endif
    lea rax, [rdi + rdi + 5]
    xor edi, edi
    xor esi, esi
    xor edx, edx
    xor ecx, ecx
    xor r8d, r8d
    xor r9d, r9d
    xor r10d, r10d
    xor r11d, r11d
    ret
.size stack_leaf, .-stack_leaf
.section .note.GNU-stack,"",@progbits
