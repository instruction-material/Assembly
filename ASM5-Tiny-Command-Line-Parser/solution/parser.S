#ifdef __APPLE__
#define GLOBAL(name) _##name
#else
#define GLOBAL(name) name
#endif

.intel_syntax noprefix
.text

.globl GLOBAL(asm_streq)
GLOBAL(asm_streq):
	xor rcx, rcx

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

.globl GLOBAL(asm_parse_i64)
GLOBAL(asm_parse_i64):
	xor rax, rax
	xor rcx, rcx
	mov r8, rsi
	mov r9d, 1

	mov dl, BYTE PTR [rdi]
	cmp dl, '-'
	jne .Lmaybe_plus
	mov r9d, -1
	inc rcx
	jmp .Lcheck_first_digit

.Lmaybe_plus:
	cmp dl, '+'
	jne .Lcheck_first_digit
	inc rcx

.Lcheck_first_digit:
	mov dl, BYTE PTR [rdi + rcx]
	test dl, dl
	je .Lparse_fail

.Lparse_loop:
	mov dl, BYTE PTR [rdi + rcx]
	test dl, dl
	je .Lapply_sign
	cmp dl, '0'
	jb .Lparse_fail
	cmp dl, '9'
	ja .Lparse_fail
	imul rax, rax, 10
	sub dl, '0'
	movzx r10, dl
	add rax, r10
	inc rcx
	jmp .Lparse_loop

.Lapply_sign:
	cmp r9d, 1
	je .Lstore_value
	neg rax

.Lstore_value:
	mov QWORD PTR [r8], rax
	mov eax, 1
	ret

.Lparse_fail:
	xor eax, eax
	ret
