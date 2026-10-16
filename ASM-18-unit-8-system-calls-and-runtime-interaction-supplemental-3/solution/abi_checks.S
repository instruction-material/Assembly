#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl abi_probe
.type abi_probe, @function
abi_probe:
    push rbp
    push rbx
    push r12
    push r13
    push r14
    push r15
    sub rsp, 24
    mov rax, rdi
    mov QWORD PTR [rsp + 8], r9
    mov rdi, rsi
    mov rsi, rdx
    mov rdx, rcx
    mov rcx, r8
    mov rbx, 0x13579bdf2468ace0
    mov rbp, 0x2468ace013579bdf
    mov r12, 0x1122334455667788
    mov r13, 0x2233445566778899
    mov r14, 0x33445566778899aa
    mov r15, 0x445566778899aabb
    call rax
    mov r11, QWORD PTR [rsp + 8]
    mov DWORD PTR [r11], 0
    mov r10, 0x13579bdf2468ace0
    cmp rbx, r10
    jne .Lprobe_done
    mov r10, 0x2468ace013579bdf
    cmp rbp, r10
    jne .Lprobe_done
    mov r10, 0x1122334455667788
    cmp r12, r10
    jne .Lprobe_done
    mov r10, 0x2233445566778899
    cmp r13, r10
    jne .Lprobe_done
    mov r10, 0x33445566778899aa
    cmp r14, r10
    jne .Lprobe_done
    mov r10, 0x445566778899aabb
    cmp r15, r10
    jne .Lprobe_done
    mov DWORD PTR [r11], 1
.Lprobe_done:
    add rsp, 24
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    pop rbp
    ret
.size abi_probe, .-abi_probe
.section .note.GNU-stack,"",@progbits
