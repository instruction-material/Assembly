#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    sub rsp, 24
    mov QWORD PTR [rsp + 0], rdi
    mov QWORD PTR [rsp + 8], rsi
    mov QWORD PTR [rsp + 16], rdx
.globl lab_call
lab_call:
    call lab_helper
.globl lab_after_call
lab_after_call:
    mov r11, QWORD PTR [rsp + 16]
    # LOCAL_RELOAD: recover initial from its own saved slot
    mov r8, QWORD PTR [rsp + 0] # saved initial
    mov r9, QWORD PTR [rsp + 8] # saved incoming
    mov QWORD PTR [r11 + 0], rax
    mov QWORD PTR [r11 + 8], r8
    mov QWORD PTR [r11 + 16], r9
    add rax, r8
    mov QWORD PTR [r11 + 24], rax
    mov QWORD PTR [r11 + 32], r10
    add rsp, 24
.globl lab_return
lab_return:
    ret
.size lab_operation, .-lab_operation
.globl lab_helper
.type lab_helper, @function
lab_helper:
    mov r10, rsp
    and r10d, 15
    mov rax, rdi
    xor rax, rsi
    xor edi, edi
    xor esi, esi
    xor edx, edx
    xor r8d, r8d
    xor r9d, r9d
.globl lab_helper_return
lab_helper_return:
    ret
.size lab_helper, .-lab_helper
.section .note.GNU-stack,"",@progbits
