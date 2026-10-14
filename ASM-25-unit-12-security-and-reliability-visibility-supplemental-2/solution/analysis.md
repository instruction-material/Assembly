# Reference reasoning for the binary comparison

Record actual compiler versions, commands, addresses and excerpts from the current build. No fixed addresses are supplied because they depend on that build and runtime.

Baseline disables C stack protection and produces an EXEC executable. Guard changes C instrumentation while keeping the EXEC control. Guard-pie retains C protection and changes the executable to DYN/PIE through both -fPIE and -pie. The handwritten leaf loop has no automatic stack guard in any profile. Its machine-code bytes should be unchanged across these controls.

A guarded C function loads and saves a TLS guard and checks it before returning, with a failure path to __stack_chk_fail. Explain the actual observed instructions; do not mistake a reference elsewhere in the executable for evidence about this function. The volatile local array makes the bounded accesses visible and does not add synchronization.

Checksums use unsigned 64-bit arithmetic. Empty and invalid counts return zero before reading memory; valid counts read exactly that many bytes. All profiles must agree for the same bytes, including wraparound cases. Derive the changed-case values independently and record their observed values. CTest, the independent model and physical page checks support the tested contract; none completes the analysis worksheet automatically.

A guard check does not validate every load/store or every pointer, and a correct handwritten routine is not proved safe merely by being linked with protected C. PIE describes position independence and executable relocation support, while runtime randomization also depends on the loader, OS and debugger settings. A binary flag or a pair of sample addresses is insufficient to establish a comprehensive security property.
