#if !defined(__linux__) || !defined(__x86_64__)
#error "Use Linux x86-64 System V."
#endif
.intel_syntax noprefix
.text
.global mystery_score
.type mystery_score, @function
mystery_score:
	mov rax, rdi
	test rax, rax
	jns .Labs_done
	neg rax

.Labs_done:
	test rax, 1
	jz .Leven_path
	lea rax, [rax + rax * 2 + 1]
	jmp .Lpost_parity

.Leven_path:
	sar rax, 1

.Lpost_parity:
	cmp rax, 40
	jg .Lhigh_path
	sub rax, 5
	ret

.Lhigh_path:
	add rax, 7
	ret
.size mystery_score, .-mystery_score
.section .note.GNU-stack,"",@progbits
