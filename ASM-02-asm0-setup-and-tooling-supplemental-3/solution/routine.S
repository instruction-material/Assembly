#include "lab.h"
.text
.p2align 2
.globl lab_answer
.type lab_answer, @function
lab_answer:
    movl $LAB_VALUE, %eax
    ret
.size lab_answer, .-lab_answer
.section .note.GNU-stack,"",@progbits
