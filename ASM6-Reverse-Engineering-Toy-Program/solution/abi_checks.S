#if !defined(__linux__) || !defined(__x86_64__)
#error "Linux x86-64 System V target required"
#endif
.intel_syntax noprefix
.text
.global preserved_mystery_ok
.type preserved_mystery_ok, @function
preserved_mystery_ok:
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
    call mystery_score
    mov r10, 0x1122334455667788
    cmp rbx, r10
    jne .Lpreserved_mystery_ok_failed
    mov r10, 0x2233445566778899
    cmp rbp, r10
    jne .Lpreserved_mystery_ok_failed
    mov r10, 0x33445566778899aa
    cmp r12, r10
    jne .Lpreserved_mystery_ok_failed
    mov r10, 0x445566778899aabb
    cmp r13, r10
    jne .Lpreserved_mystery_ok_failed
    mov r10, 0x5566778899aabbcc
    cmp r14, r10
    jne .Lpreserved_mystery_ok_failed
    mov r10, 0x66778899aabbccdd
    cmp r15, r10
    jne .Lpreserved_mystery_ok_failed
    mov eax, 1
    jmp .Lpreserved_mystery_ok_restore
.Lpreserved_mystery_ok_failed:
    xor eax, eax
.Lpreserved_mystery_ok_restore:
    add rsp, 8
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    pop rbx
    ret
.size preserved_mystery_ok, .-preserved_mystery_ok
.section .note.GNU-stack,"",@progbits

#if !defined(__linux__) || !defined(__x86_64__)
#error "Linux x86-64 System V target required"
#endif
.intel_syntax noprefix
.text
.global preserved_reconstruction_ok
.type preserved_reconstruction_ok, @function
preserved_reconstruction_ok:
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
    call student_reconstruction
    mov r10, 0x1122334455667788
    cmp rbx, r10
    jne .Lpreserved_reconstruction_ok_failed
    mov r10, 0x2233445566778899
    cmp rbp, r10
    jne .Lpreserved_reconstruction_ok_failed
    mov r10, 0x33445566778899aa
    cmp r12, r10
    jne .Lpreserved_reconstruction_ok_failed
    mov r10, 0x445566778899aabb
    cmp r13, r10
    jne .Lpreserved_reconstruction_ok_failed
    mov r10, 0x5566778899aabbcc
    cmp r14, r10
    jne .Lpreserved_reconstruction_ok_failed
    mov r10, 0x66778899aabbccdd
    cmp r15, r10
    jne .Lpreserved_reconstruction_ok_failed
    mov eax, 1
    jmp .Lpreserved_reconstruction_ok_restore
.Lpreserved_reconstruction_ok_failed:
    xor eax, eax
.Lpreserved_reconstruction_ok_restore:
    add rsp, 8
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    pop rbx
    ret
.size preserved_reconstruction_ok, .-preserved_reconstruction_ok
.section .note.GNU-stack,"",@progbits
