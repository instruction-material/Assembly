#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    cmp rdi, rsi
    mov eax, 0
.globl lab_stage0
lab_stage0:
    setb al
    mov QWORD PTR [rdx + 0], rax
    cmp rdi, rsi
    mov eax, 0
.globl lab_stage1
lab_stage1:
    setbe al
    mov QWORD PTR [rdx + 8], rax
    cmp rdi, rsi
    mov eax, 0
.globl lab_stage2
lab_stage2:
    # COMPARE_SIGNED: use the signed less condition
    setl al
    mov QWORD PTR [rdx + 16], rax
    cmp rdi, rsi
    mov eax, 0
.globl lab_stage3
lab_stage3:
    setle al
    mov QWORD PTR [rdx + 24], rax
    cmp rdi, rsi
    mov eax, 0
.globl lab_stage4
lab_stage4:
    sete al
    mov QWORD PTR [rdx + 32], rax
    cmp rdi, rsi
    mov eax, 0
.globl lab_stage5
lab_stage5:
    setne al
    mov QWORD PTR [rdx + 40], rax
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
