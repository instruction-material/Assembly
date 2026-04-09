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
	cmp dl, '/'
	je .Ldiv
	cmp dl, '&'
	je .Land
	cmp dl, '^'
	je .Lxor
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

.Ldiv:
	test rsi, rsi
	je .Lunsupported
	mov rax, rdi
	cqo
	idiv rsi
	ret

.Land:
	mov rax, rdi
	and rax, rsi
	ret

.Lxor:
	mov rax, rdi
	xor rax, rsi
	ret

.Lunsupported:
	xor eax, eax
	ret
