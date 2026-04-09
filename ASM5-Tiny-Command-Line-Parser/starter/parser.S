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
	mov dl, BYTE PTR [rdi]
	test dl, dl
	je .Lparse_fail

.Lparse_loop:
	mov dl, BYTE PTR [rdi + rcx]
	test dl, dl
	je .Lparse_success
	cmp dl, '0'
	jb .Lparse_fail
	cmp dl, '9'
	ja .Lparse_fail
	imul rax, rax, 10
	sub dl, '0'
	movzx r9, dl
	add rax, r9
	inc rcx
	jmp .Lparse_loop

.Lparse_success:
	mov QWORD PTR [r8], rax
	mov eax, 1
	ret

.Lparse_fail:
	xor eax, eax
	ret
