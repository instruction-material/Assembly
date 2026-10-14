# Binary hardening evidence worksheet

This is the required work. The supplied program already runs correctly.

1. TODO TARGET: Record OS, architecture, compiler version, optimization level and all three configure commands.
2. TODO PREDICT: Predict C guard instrumentation, handwritten guard instrumentation and ELF type for each profile before inspecting.
3. TODO CONTRACT: Derive checksums for Assembly, ABC, empty input and 32 bytes; state unsigned wraparound and byte-count limits.
4. TODO STATIC: Record actual function-scoped excerpts showing the C guard load, saved value, check and failure path. Compare the unprotected C function and the leaf assembly.
5. TODO ELF: Record baseline/guard/guard-pie ELF types with the compile/link evidence that identifies the PIE executable.
6. TODO CHANGED: Pass the same changed cases under both compilers and optimization levels. Record which evidence changed and which behavior did not.
7. TODO LIMITS: Explain why stack guarding, bounds checks, pointer validity, PIE, ASLR and functional correctness establish different facts.
