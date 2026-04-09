#ifdef __APPLE__
#define GLOBAL(name) _##name
#else
#define GLOBAL(name) name
#endif

.intel_syntax noprefix
.text

.globl GLOBAL(mystery_score)
GLOBAL(mystery_score):
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
