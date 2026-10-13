#if !defined(__linux__) || !defined(__x86_64__)
#error "Linux x86-64 System V target required"
#endif
.intel_syntax noprefix
.text
.global preserved_helper_ok
.type preserved_helper_ok, @function
preserved_helper_ok:
    push rbx
    push rbp
    push r12
    push r13
    push r14
    push r15
    sub rsp, 8
    mov rbx, 0x1122334455667788
    mov rbp, 0x2233445566778899
    mov r12, 0x33445566778899aa
    mov r13, 0x445566778899aabb
    mov r14, 0x5566778899aabbcc
    mov r15, 0x66778899aabbccdd
    call asm_scaled_clamped_sum
    mov r10, 0x1122334455667788
    cmp rbx, r10
    jne .Lfailed
    mov r10, 0x2233445566778899
    cmp rbp, r10
    jne .Lfailed
    mov r10, 0x33445566778899aa
    cmp r12, r10
    jne .Lfailed
    mov r10, 0x445566778899aabb
    cmp r13, r10
    jne .Lfailed
    mov r10, 0x5566778899aabbcc
    cmp r14, r10
    jne .Lfailed
    mov r10, 0x66778899aabbccdd
    cmp r15, r10
    jne .Lfailed
    mov eax, 1
    jmp .Lrestore
.Lfailed:
    xor eax, eax
.Lrestore:
    add rsp, 8
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    pop rbx
    ret
.size preserved_helper_ok, .-preserved_helper_ok
.section .note.GNU-stack,"",@progbits

.text
.global clamp_to_range
.type clamp_to_range, @function
clamp_to_range:
    inc QWORD PTR [rip + helper_call_count]
    mov QWORD PTR [rip + helper_value], rdi
    mov QWORD PTR [rip + helper_min], rsi
    mov QWORD PTR [rip + helper_max], rdx
    mov r10, rsp
    and r10, 15
    mov QWORD PTR [rip + helper_stack_mod], r10
    jmp clamp_implementation
.size clamp_to_range, .-clamp_to_range
.section .note.GNU-stack,"",@progbits
