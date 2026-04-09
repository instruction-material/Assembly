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
	mov rax, rcx
	ret

.Lcopy_success:
	mov rax, rcx
	ret

.Lcopy_done:
	xor eax, eax
	ret
