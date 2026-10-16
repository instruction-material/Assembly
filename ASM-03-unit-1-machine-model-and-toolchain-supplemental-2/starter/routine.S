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
    xor eax, eax
.globl lab_stage0
lab_stage0:
    movzx eax, BYTE PTR [rsp + 0]
    mov QWORD PTR [rdx + 0], rax
.globl lab_stage1
lab_stage1:
    movzx eax, WORD PTR [rsp + 1]
    mov QWORD PTR [rdx + 8], rax
.globl lab_stage2
lab_stage2:
    mov eax, DWORD PTR [rsp + 4]
    mov QWORD PTR [rdx + 16], rax
.globl lab_stage3
lab_stage3:
    mov rax, QWORD PTR [rsp + 0]
    mov QWORD PTR [rdx + 24], rax
.globl lab_stage4
lab_stage4:
    # MEMORY_SPAN: load all eight bytes beginning at offset 3
    mov eax, DWORD PTR [rsp + 3]
    mov QWORD PTR [rdx + 32], rax
.globl lab_stage5
lab_stage5:
    mov rax, QWORD PTR [rsp + 8]
    mov QWORD PTR [rdx + 40], rax
    add rsp, 24
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
