#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    mov rcx, rdi
    and ecx, 3
    xor r8d, r8d
    mov r9d, 1
.globl lab_check0
lab_check0:
    cmp ecx, 0
    je lab_case0
    mov r9d, 2
.globl lab_check1
lab_check1:
    cmp ecx, 1
    je lab_case1
    mov r9d, 3
.globl lab_check2
lab_check2:
    cmp ecx, 2
    je lab_case2
    jmp lab_case3
.globl lab_case0
lab_case0:
    or r8d, 1
    lea rax, [rsi + 11]
    jmp lab_join
.globl lab_case1
lab_case1:
    or r8d, 2
    mov rax, rsi
    xor rax, 0x55
    # DISPATCH_JOIN: leave the selected case before the next case starts
    nop # selected-case exit remains incomplete
.globl lab_case2
lab_case2:
    or r8d, 4
    lea rax, [rsi - 7]
    jmp lab_join
.globl lab_case3
lab_case3:
    or r8d, 8
    mov rax, rsi
.globl lab_join
lab_join:
    mov QWORD PTR [rdx + 0], rcx
    mov QWORD PTR [rdx + 8], rax
    mov QWORD PTR [rdx + 16], r8
    mov QWORD PTR [rdx + 24], r9
.globl lab_return
lab_return:
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
