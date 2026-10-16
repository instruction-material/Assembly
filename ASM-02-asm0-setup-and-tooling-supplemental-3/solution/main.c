#include "lab.h"
#include <stdio.h>

int main(void) {
    const int actual = lab_answer();
    printf("answer=%d\n", actual);
    return actual == LAB_VALUE ? 0 : 1;
}
