#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 System V for this project."
#endif
.intel_syntax noprefix
.text
.global decode_record
.type decode_record, @function
decode_record:
    /* TODO RECORD_DECODE: check the four-argument contract, calculate the
       selected address and load the three fields with their stated widths.
       Keep rejected calls free of record reads and output writes. */
    xor eax, eax
    ret
.size decode_record, .-decode_record
.section .note.GNU-stack,"",@progbits
