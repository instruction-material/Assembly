#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    mov rax, rdi
.globl lab_stage0
lab_stage0:
    # SIGN_BYTE: extend the byte's signed interpretation to all 64 bits
    movsx rax, sil
    mov QWORD PTR [rdx + 0], rax
    mov rax, rdi
.globl lab_stage1
lab_stage1:
    movzx eax, sil
    mov QWORD PTR [rdx + 8], rax
    mov rax, rdi
.globl lab_stage2
lab_stage2:
    movsx rax, si
    mov QWORD PTR [rdx + 16], rax
    mov rax, rdi
.globl lab_stage3
lab_stage3:
    movzx eax, si
    mov QWORD PTR [rdx + 24], rax
    mov rax, rdi
.globl lab_stage4
lab_stage4:
    movsxd rax, esi
    mov QWORD PTR [rdx + 32], rax
    mov rax, rdi
.globl lab_stage5
lab_stage5:
    mov eax, esi
    mov QWORD PTR [rdx + 40], rax
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
