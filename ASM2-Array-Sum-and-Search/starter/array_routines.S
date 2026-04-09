#ifdef __APPLE__
#define GLOBAL(name) _##name
#else
#define GLOBAL(name) name
#endif

.intel_syntax noprefix
.text

.globl GLOBAL(asm_sum_array)
GLOBAL(asm_sum_array):
	xor rax, rax
	xor rcx, rcx

.Lsum_loop:
	cmp rcx, rsi
	jge .Lsum_done
	movsxd r8, DWORD PTR [rdi + rcx * 4]
	add rax, r8
	inc rcx
	jmp .Lsum_loop

.Lsum_done:
	ret

.globl GLOBAL(asm_find_first_ge)
GLOBAL(asm_find_first_ge):
	mov rax, -1
	ret
