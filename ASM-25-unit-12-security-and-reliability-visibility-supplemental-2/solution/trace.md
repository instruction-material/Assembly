# Reference reasoning for the runtime investigation

Use actual baseline and guard-pie binaries from the static analysis. With the default input, both entry traces must receive eight bytes and return the independently predicted checksum. At a valid C entry, follow the generated guard setup and ordinary return-check path. The failure call is a possible path in disassembly; do not claim it executed during a successful run.

The handwritten entry follows explicit count checks, the byte loop and the return. It has no compiler-added guard. Repeat with ABC (three bytes) or the empty argument (zero bytes and return zero); show the actual branch difference and confirm the same two implementations still agree.

Record the actual addresses and debugger settings. The PIE executable can be relocated, but load addresses also depend on the runtime and debugger. GDB's disable-randomization off leaves the inferior's randomization enabled; warnings or host policy can constrain that request. Do not infer a machine-wide policy from two sampled addresses. Keep the static experiment and the runtime trace as distinct pieces of evidence.
