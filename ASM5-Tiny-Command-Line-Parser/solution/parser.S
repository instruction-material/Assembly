#if !defined(__linux__) || !defined(__x86_64__)
#error "Use the Linux x86-64 System V target."
#endif
.intel_syntax noprefix
.text
.global asm_streq
.type asm_streq, @function
asm_streq:
    xor ecx, ecx
.Lstreq_loop:
    mov al, BYTE PTR [rdi + rcx]
    mov dl, BYTE PTR [rsi + rcx]
    cmp al, dl
    jne .Lstreq_no
    test al, al
    je .Lstreq_yes
    inc rcx
    jmp .Lstreq_loop
.Lstreq_yes:
    mov eax, 1
    ret
.Lstreq_no:
    xor eax, eax
    ret
.size asm_streq, .-asm_streq

.global asm_parse_i64
.type asm_parse_i64, @function
asm_parse_i64:
    xor eax, eax
    xor ecx, ecx
    mov r8, rsi
    xor r9d, r9d
    mov r11d, 7
    mov r10, 922337203685477580
    mov dl, BYTE PTR [rdi]
    cmp dl, '-'
    jne .Lmaybe_plus
    mov r9d, 1
    mov r11d, 8
    inc rcx
    jmp .Lfirst_digit
.Lmaybe_plus:
    cmp dl, '+'
    jne .Lfirst_digit
    inc rcx
.Lfirst_digit:
    cmp BYTE PTR [rdi + rcx], 0
    je .Lparse_fail
.Lparse_loop:
    movzx edx, BYTE PTR [rdi + rcx]
    test dl, dl
    je .Lapply_sign
    cmp dl, '0'
    jb .Lparse_fail
    cmp dl, '9'
    ja .Lparse_fail
    sub edx, '0'
    cmp rax, r10
    ja .Lparse_fail
    jb .Ldigit_fits
    cmp edx, r11d
    ja .Lparse_fail
.Ldigit_fits:
    imul rax, rax, 10
    add rax, rdx
    inc rcx
    jmp .Lparse_loop
.Lapply_sign:
    test r9d, r9d
    je .Lstore_value
    neg rax
.Lstore_value:
    mov QWORD PTR [r8], rax
    mov eax, 1
    ret
.Lparse_fail:
    xor eax, eax
    ret
.size asm_parse_i64, .-asm_parse_i64
.section .note.GNU-stack,"",@progbits
