#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    sub rsp, 16
    mov rax, 0x0807060504030201
    mov QWORD PTR [rsp], rax
    mov rax, 0x100f0e0d0c0b0a09
    mov QWORD PTR [rsp + 8], rax
    mov r8, rdi
    and r8d, 7
    mov r9, rsi
    and r9d, 7
    mov rcx, rdi
    shr rcx, 3
    and ecx, 15
    mov r10d, 16
    sub r10, r8
    cmp rcx, r10
    cmova rcx, r10
    mov r10d, 16
    sub r10, r9
    cmp rcx, r10
    cmova rcx, r10
    mov QWORD PTR [rdx + 16], rcx
    mov QWORD PTR [rdx + 24], r8
    mov QWORD PTR [rdx + 32], r9
.globl lab_ready
lab_ready:
    test rcx, rcx
    jz lab_copy_done
.globl lab_direction
lab_direction:
    cmp r9, r8
    # COPY_DIRECTION: a higher destination uses the backward loop
    ja lab_backward
lab_forward:
.globl lab_forward_load
lab_forward_load:
    mov al, BYTE PTR [rsp + r8]
.globl lab_forward_store
lab_forward_store:
    mov BYTE PTR [rsp + r9], al
    inc r8
    inc r9
    dec rcx
    jnz lab_forward_load
    jmp lab_copy_done
lab_backward:
    add r8, rcx
    dec r8
    add r9, rcx
    dec r9
.globl lab_backward_load
lab_backward_load:
    mov al, BYTE PTR [rsp + r8]
.globl lab_backward_store
lab_backward_store:
    mov BYTE PTR [rsp + r9], al
    dec r8
    dec r9
    dec rcx
    jnz lab_backward_load
.globl lab_copy_done
lab_copy_done:
    mov rax, QWORD PTR [rsp]
    mov QWORD PTR [rdx], rax
    mov rax, QWORD PTR [rsp + 8]
    mov QWORD PTR [rdx + 8], rax
    add rsp, 16
.globl lab_return
lab_return:
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
