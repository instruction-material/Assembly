#ifndef OWNED_SYSCALL_LAB_H
#define OWNED_SYSCALL_LAB_H
_Static_assert(sizeof(long) == 8 && sizeof(void *) == 8, "Use the Linux x86-64 LP64 target");
long lab_write(long fd, const void *buffer, unsigned long count);
long abi_probe(long (*function)(long, const void *, unsigned long), long fd, const void *buffer, unsigned long count, int *preserved);
#endif
