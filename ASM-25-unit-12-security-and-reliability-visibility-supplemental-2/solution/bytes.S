#if !defined(__linux__) || !defined(__x86_64__)
#error "Linux x86-64 System V target required"
#endif
.intel_syntax noprefix
.text
.global checksum_asm
.type checksum_asm, @function
checksum_asm:
    test rsi, rsi
    jle .Lchecksum_none
    cmp rsi, 32
    jg .Lchecksum_none
    mov eax, 5381
    xor ecx, ecx
.Lchecksum_loop:
    cmp rcx, rsi
    jge .Lchecksum_done
    imul rax, rax, 33
    movzx edx, BYTE PTR [rdi+rcx]
    add rax, rdx
    inc rcx
    jmp .Lchecksum_loop
.Lchecksum_done:
    ret
.Lchecksum_none:
    xor eax, eax
    ret
.size checksum_asm, .-checksum_asm
.section .note.GNU-stack,"",@progbits
