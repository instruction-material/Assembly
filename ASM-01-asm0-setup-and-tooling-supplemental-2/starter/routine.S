#include "lab.h"
.text
.p2align 2
# TODO: export lab_answer to the separately compiled C caller
.type lab_answer, @function
lab_answer:
    movl $LAB_VALUE, %eax
    ret
.size lab_answer, .-lab_answer
.section .note.GNU-stack,"",@progbits
