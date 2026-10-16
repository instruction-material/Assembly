#ifndef SETUP_LAB_H
#define SETUP_LAB_H
#ifndef LAB_VALUE
#define LAB_VALUE 41
#endif
#ifndef __ASSEMBLER__
_Static_assert(LAB_VALUE >= 0 && LAB_VALUE <= 255, "LAB_VALUE range");
int lab_answer(void);
#endif
#endif
