#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    mov r11, rsp
    push rdi # save initial first
    push rsi # save incoming second
.globl lab_pops
lab_pops:
    # LIFO_POP: the most recently pushed value belongs in RAX
    pop rax # incoming
    pop rcx # initial
.globl lab_restored
lab_restored:
    mov r8, rsp
    sub r8, r11
    mov r9, rcx
    sub r9, rax
    mov QWORD PTR [rdx + 0], rax
    mov QWORD PTR [rdx + 8], rcx
    mov QWORD PTR [rdx + 16], r9
    mov QWORD PTR [rdx + 24], r8
.globl lab_return
lab_return:
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
