#if !defined(__linux__) || !defined(__x86_64__)
#error "Use the Linux x86-64 System V target."
#endif
.intel_syntax noprefix
.text

.global asm_strlen_simple
.type asm_strlen_simple, @function
asm_strlen_simple:
	xor rax, rax

.Lstrlen_loop:
	mov dl, BYTE PTR [rdi + rax]
	test dl, dl
	je .Lstrlen_done
	inc rax
	jmp .Lstrlen_loop

.Lstrlen_done:
	ret

.size asm_strlen_simple, .-asm_strlen_simple

.global asm_strlcpy_simple
.type asm_strlcpy_simple, @function
asm_strlcpy_simple:
	xor rcx, rcx
	test rdx, rdx
	je .Lcopy_done

.Lcopy_loop:
	cmp rcx, rdx
	jae .Lterminate
	lea r8, [rdx - 1]
	cmp rcx, r8
	jae .Lterminate
	mov al, BYTE PTR [rsi + rcx]
	mov BYTE PTR [rdi + rcx], al
	test al, al
	je .Lcopy_success
	inc rcx
	jmp .Lcopy_loop

.Lterminate:
	mov BYTE PTR [rdi + rcx], 0
	jmp .Lcount_tail

.Lcopy_success:
	mov rax, rcx
	ret

.Lcopy_done:
	xor ecx, ecx

.Lcount_tail:
	/* TODO COPY_SOURCE_LENGTH: count the remaining source bytes to NUL.
	   Do not write more destination bytes; return the full source length. */
	mov rax, rcx
	ret

.size asm_strlcpy_simple, .-asm_strlcpy_simple
.section .note.GNU-stack,"",@progbits
