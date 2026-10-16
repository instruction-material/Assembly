#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    mov rax, rdi
    mov rcx, rsi
.globl lab_stage0
lab_stage0:
    shl rax, cl
    mov QWORD PTR [rdx + 0], rax
    mov rax, rdi
    mov rcx, rsi
.globl lab_stage1
lab_stage1:
    shr rax, cl
    mov QWORD PTR [rdx + 8], rax
    mov rax, rdi
    mov rcx, rsi
.globl lab_stage2
lab_stage2:
    # SHIFT_SIGNED: preserve the signed interpretation while shifting right
    sar rax, cl
    mov QWORD PTR [rdx + 16], rax
    mov rax, rsi
.globl lab_stage3
lab_stage3:
    and eax, 63
    mov QWORD PTR [rdx + 24], rax
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
