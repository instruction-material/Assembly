#if !defined(__linux__) || !defined(__x86_64__)
#error "Use the Linux x86-64 System V target."
#endif
.intel_syntax noprefix
.text
.global asm_sum_array
.type asm_sum_array, @function
asm_sum_array:
    xor eax, eax
    xor ecx, ecx
.Lsum_loop:
    cmp rcx, rsi
    jge .Lsum_done
    movsxd r8, DWORD PTR [rdi + rcx * 4]
    add rax, r8
    inc rcx
    jmp .Lsum_loop
.Lsum_done:
    ret
.size asm_sum_array, .-asm_sum_array

.global asm_find_first_ge
.type asm_find_first_ge, @function
asm_find_first_ge:
    /* TODO ARRAY_SEARCH: return the first signed >= threshold index, or -1.
       Stop before reading values[count]; count <= 0 does not read values. */
    mov rax, -1
    ret
.size asm_find_first_ge, .-asm_find_first_ge
.section .note.GNU-stack,"",@progbits
