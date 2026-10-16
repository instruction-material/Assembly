#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    mov eax, 0
    cmp rdi, rsi
.globl lab_stage0
lab_stage0:
    lea rax, [rdi + rsi]
    mov QWORD PTR [rdx + 0], rax
.globl lab_stage1
lab_stage1:
    lea rax, [rdi + rsi*2]
    mov QWORD PTR [rdx + 8], rax
.globl lab_stage2
lab_stage2:
    # ADDRESS_SCALE: use the documented four-byte index scale
    lea rax, [rdi + rsi*2 + 13]
    mov QWORD PTR [rdx + 16], rax
.globl lab_stage3
lab_stage3:
    lea rax, [rdi + rsi*8 - 7]
    mov QWORD PTR [rdx + 24], rax
.globl lab_stage4
lab_stage4:
    lea rax, [rsi*8]
    mov QWORD PTR [rdx + 32], rax
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
