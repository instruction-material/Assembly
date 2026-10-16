#ifndef OWNED_SYSCALL_LAB_H
#define OWNED_SYSCALL_LAB_H
_Static_assert(sizeof(long) == 8 && sizeof(void *) == 8, "Use the Linux x86-64 LP64 target");
long lab_openat(long directory, const char *path, long flags, unsigned long mode);
long abi_probe(long (*function)(long, const char *, long, unsigned long), long directory, const char *path, long flags, unsigned long mode, int *preserved);
#endif
