#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    sub rsp, 24
    mov QWORD PTR [rsp + 0], rdx
    mov QWORD PTR [rsp + 8], rdi
    mov QWORD PTR [rsp + 16], rsi
    mov rdx, rdi
    xor rdx, rsi
    mov rcx, rdi
    add rcx, rsi
    # ARGUMENT_REGISTER: prepare the fifth integer argument from initial
    mov r8, rsi # incomplete fifth argument before complement
    not r8
    mov r9, rsi
    not r9
.globl lab_call
lab_call:
    call lab_helper
.globl lab_after_call
lab_after_call:
    mov r11, QWORD PTR [rsp + 0]
    mov r8, QWORD PTR [rsp + 8]
    mov r9, QWORD PTR [rsp + 16]
    mov QWORD PTR [r11 + 0], rax
    mov QWORD PTR [r11 + 8], r8
    mov QWORD PTR [r11 + 16], r9
    add rsp, 24
.globl lab_return
lab_return:
    ret
.size lab_operation, .-lab_operation
.globl lab_helper
.type lab_helper, @function
lab_helper:
    mov rax, rdi
    imul r10, rsi, 3
    add rax, r10
    imul r10, rdx, 5
    add rax, r10
    imul r10, rcx, 7
    add rax, r10
    imul r10, r8, 11
    add rax, r10
    imul r10, r9, 13
    add rax, r10
    xor edi, edi
    xor esi, esi
    xor edx, edx
    xor ecx, ecx
    xor r8d, r8d
    xor r9d, r9d
    xor r10d, r10d
    xor r11d, r11d
.globl lab_helper_return
lab_helper_return:
    ret
.size lab_helper, .-lab_helper
.section .note.GNU-stack,"",@progbits
