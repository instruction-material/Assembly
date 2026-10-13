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
	je .Lcount_only

.Lcopy_loop:
	lea r8, [rdx - 1]
	cmp rcx, r8
	jae .Lfinish_copy
	mov al, BYTE PTR [rsi + rcx]
	mov BYTE PTR [rdi + rcx], al
	test al, al
	je .Lreturn_length
	inc rcx
	jmp .Lcopy_loop

.Lfinish_copy:
	mov BYTE PTR [rdi + rcx], 0

.Lcount_tail:
	mov al, BYTE PTR [rsi + rcx]
	test al, al
	je .Lreturn_length
	inc rcx
	jmp .Lcount_tail

.Lcount_only:
	xor rcx, rcx

.Lcount_only_loop:
	mov al, BYTE PTR [rsi + rcx]
	test al, al
	je .Lreturn_length
	inc rcx
	jmp .Lcount_only_loop

.Lreturn_length:
	mov rax, rcx
	ret

.size asm_strlcpy_simple, .-asm_strlcpy_simple
.section .note.GNU-stack,"",@progbits
