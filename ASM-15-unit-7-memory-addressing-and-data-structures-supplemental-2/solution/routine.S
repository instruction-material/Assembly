#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    sub rsp, 96
    mov r8, rsp
    mov r10, rsi
    and r10d, 3
    xor ecx, ecx
lab_initialize:
    mov rax, rsi
    add rax, rcx
    mov QWORD PTR [r8], rax
    imul eax, ecx, 0x1111
    xor eax, esi
    mov WORD PTR [r8 + 8], ax
    mov BYTE PTR [r8 + 10], cl
    mov BYTE PTR [r8 + 11], 0xa5
    mov rax, rsi
    shr rax, 16
    imul r9d, ecx, 0x01010101
    xor eax, r9d
    mov DWORD PTR [r8 + 12], eax
    mov r9, rcx
    add r9, r10
    and r9d, 3
    shl r9, 4
    add r9, rsp
    mov QWORD PTR [rsp + rcx*8 + 64], r9
    add r8, 16
    inc ecx
    cmp ecx, 4
    jne lab_initialize
    mov rax, rdi
    and eax, 3
.globl lab_lookup
lab_lookup:
    # POINTER_LOOKUP: select the pointer slot for the masked index
    mov r8, QWORD PTR [rsp + rax*8 + 64]
.globl lab_selected
lab_selected:
    mov QWORD PTR [rdx + 0], rax
    movzx r9d, BYTE PTR [r8 + 10]
    mov QWORD PTR [rdx + 8], r9
    mov r9d, DWORD PTR [r8 + 12]
    mov QWORD PTR [rdx + 16], r9
    movzx r9d, WORD PTR [r8 + 8]
    mov QWORD PTR [rdx + 24], r9
    sub r8, rsp
    mov QWORD PTR [rdx + 32], r8
    add rsp, 96
.globl lab_return
lab_return:
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
