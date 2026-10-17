#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 with the System V AMD64 ABI."
#endif
.intel_syntax noprefix
.text
.globl lab_operation
.type lab_operation, @function
lab_operation:
    and edi, 15
    xor ecx, ecx
    xor eax, eax
    xor r8d, r8d
    xor r9d, r9d
.globl lab_check
lab_check:
    cmp rcx, rdi
    # LOOP_EXIT: stop before executing the body at index == count
    jae lab_join
.globl lab_body
lab_body:
    bts r8, rcx
    add rax, rsi
    inc r9
    inc rcx
    jmp lab_check
.globl lab_join
lab_join:
    mov QWORD PTR [rdx + 0], rdi
    mov QWORD PTR [rdx + 8], rax
    mov QWORD PTR [rdx + 16], r9
    mov QWORD PTR [rdx + 24], r8
    mov QWORD PTR [rdx + 32], rcx
.globl lab_return
lab_return:
    ret
.size lab_operation, .-lab_operation
.section .note.GNU-stack,"",@progbits
