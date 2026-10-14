#if !defined(__linux__) || !defined(__x86_64__)
#error "Linux x86-64 System V target required"
#endif
.intel_syntax noprefix
.text
.global sum_nonnegative_branch
.type sum_nonnegative_branch, @function
sum_nonnegative_branch:
    .cfi_startproc
    xor eax, eax
    test rsi, rsi
    jle .Lbranch_done
    xor ecx, ecx
.Lbranch_loop:
    mov r8, QWORD PTR [rdi+rcx*8]
    test r8, r8
performance_branch_decision:
    jns .Lbranch_add
performance_branch_advance:
    inc rcx
    cmp rcx, rsi
    jl .Lbranch_loop
    jmp .Lbranch_done
.Lbranch_add:
    add rax, r8
    jmp performance_branch_advance
.Lbranch_done:
    ret
    .cfi_endproc
.size sum_nonnegative_branch, .-sum_nonnegative_branch

.global sum_nonnegative_cmov
.type sum_nonnegative_cmov, @function
sum_nonnegative_cmov:
    .cfi_startproc
    xor eax, eax
    test rsi, rsi
    jle .Lcmov_done
    xor ecx, ecx
.Lcmov_loop:
    mov r8, QWORD PTR [rdi+rcx*8]
    xor r9d, r9d
    test r8, r8
    cmovns r9, r8
    add rax, r9
    inc rcx
    cmp rcx, rsi
    jl .Lcmov_loop
.Lcmov_done:
    ret
    .cfi_endproc
.size sum_nonnegative_cmov, .-sum_nonnegative_cmov

.global sum_nonnegative_indexed
.type sum_nonnegative_indexed, @function
sum_nonnegative_indexed:
    .cfi_startproc
    xor eax, eax
    test rdx, rdx
    jle .Lindexed_done
    xor ecx, ecx
.Lindexed_loop:
    mov r8, QWORD PTR [rsi+rcx*8]
    mov r9, QWORD PTR [rdi+r8*8]
    test r9, r9
    js .Lindexed_advance
    add rax, r9
.Lindexed_advance:
    inc rcx
    cmp rcx, rdx
    jl .Lindexed_loop
.Lindexed_done:
    ret
    .cfi_endproc
.size sum_nonnegative_indexed, .-sum_nonnegative_indexed
.section .note.GNU-stack,"",@progbits
