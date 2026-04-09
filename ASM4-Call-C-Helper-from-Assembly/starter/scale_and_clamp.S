#ifdef __APPLE__
#define GLOBAL(name) _##name
#else
#define GLOBAL(name) name
#endif

.intel_syntax noprefix
.text

.globl GLOBAL(asm_scaled_clamped_sum)
GLOBAL(asm_scaled_clamped_sum):
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
	ret
