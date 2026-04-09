#ifdef __APPLE__
#define GLOBAL(name) _##name
#else
#define GLOBAL(name) name
#endif

.intel_syntax noprefix
.text

.globl GLOBAL(asm_eval_expression)
GLOBAL(asm_eval_expression):
	cmp dl, '+'
	je .Ladd
	cmp dl, '-'
	je .Lsub
	cmp dl, '*'
	je .Lmul
	xor eax, eax
	ret

.Ladd:
	mov rax, rdi
	add rax, rsi
	ret

.Lsub:
	mov rax, rdi
	sub rax, rsi
	ret

.Lmul:
	mov rax, rdi
	imul rax, rsi
	ret
