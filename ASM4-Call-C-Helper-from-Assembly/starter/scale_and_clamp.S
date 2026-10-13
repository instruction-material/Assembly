#if !defined(__linux__) || !defined(__x86_64__)
#error "Use the Linux x86-64 System V target."
#endif
.intel_syntax noprefix
.text

.global asm_scaled_clamped_sum
.type asm_scaled_clamped_sum, @function
asm_scaled_clamped_sum:
	xor rax, rax
	xor r9, r9

.Lsum_loop:
	cmp r9, rsi
	jge .Lsum_done
	movsxd r10, DWORD PTR [rdi + r9 * 4]
	add rax, r10
	inc r9
	jmp .Lsum_loop

.Lsum_done:
	imul rax, rdx
	/* TODO CALL_CLAMP: align the stack, map the three C arguments,
	   call clamp_to_range, and restore the stack before returning. */
	ret

.size asm_scaled_clamped_sum, .-asm_scaled_clamped_sum
.section .note.GNU-stack,"",@progbits
