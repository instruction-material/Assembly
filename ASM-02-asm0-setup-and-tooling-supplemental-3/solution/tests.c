#include "lab.h"
#include <stdio.h>

int main(void) {
    const int actual = lab_answer();
    if (actual != LAB_VALUE) {
        fprintf(stderr, "expected %d, observed %d\n", LAB_VALUE, actual);
        return 1;
    }
    puts("configured value observed through the linked function");
    return 0;
}
