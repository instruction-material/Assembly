#ifdef __APPLE__
#define GLOBAL(name) _##name
#else
#define GLOBAL(name) name
#endif

.intel_syntax noprefix
.text

.globl GLOBAL(asm_strlen_simple)
GLOBAL(asm_strlen_simple):
	xor rax, rax

.Lstrlen_loop:
	mov dl, BYTE PTR [rdi + rax]
	test dl, dl
	je .Lstrlen_done
	inc rax
	jmp .Lstrlen_loop

.Lstrlen_done:
	ret

.globl GLOBAL(asm_strlcpy_simple)
GLOBAL(asm_strlcpy_simple):
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
