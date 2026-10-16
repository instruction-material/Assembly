#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    # WIDTH_SEED: retain the full initial register before the byte write
    mov eax, edi
.globl lab_stage0
lab_stage0:
    mov al, sil
    mov QWORD PTR [rdx + 0], rax
    mov rax, rdi
.globl lab_stage1
lab_stage1:
    mov ax, si
    mov QWORD PTR [rdx + 8], rax
    mov rax, rdi
.globl lab_stage2
lab_stage2:
    mov eax, esi
    mov QWORD PTR [rdx + 16], rax
    mov rax, rdi
.globl lab_stage3
lab_stage3:
    mov rax, rsi
    mov QWORD PTR [rdx + 24], rax
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
