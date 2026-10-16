#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 System V for this project."
#endif
.intel_syntax noprefix
.text
.global decode_record
.type decode_record, @function
decode_record:
    xor eax, eax
    test rdi, rdi
    jz .Ldone
    test rcx, rcx
    jz .Ldone
    cmp rdx, rsi
    jae .Ldone
    /* LEA computes the address without reading its bytes. */
    lea r8, [rdi + rdx*8]
    mov qword ptr [rcx], r8
.global record_signed_load
record_signed_load:
    movsx r9, word ptr [r8]
    mov qword ptr [rcx + 8], r9
.global record_unsigned_load
record_unsigned_load:
    movzx r9d, word ptr [r8 + 2]
    mov qword ptr [rcx + 16], r9
.global record_tag_load
record_tag_load:
    mov r9d, dword ptr [r8 + 4]
    mov qword ptr [rcx + 24], r9
    mov eax, 1
.Ldone:
    ret
.size decode_record, .-decode_record
.section .note.GNU-stack,"",@progbits
