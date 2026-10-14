# Runtime Hardening Trace Companion

This optional investigation follows the Binary Hardening Evidence Lab in the sibling ASM-25-unit-12-security-and-reliability-visibility-supplemental-2 folder. It extends the static comparison with actual entry registers, executed control flow, return values and debugger-policy observations. It does not introduce a second arithmetic implementation.

Read that lab's complete README first, build its baseline and guard-pie profiles on Linux x86-64, and pass their CTest contracts. Its starter and solution folders contain the complete program and trace worksheets. The starter/trace.md and solution/trace.md files here are exact copies for preserving a separate first attempt and reference comparison. Follow the GDB commands in the lab guide, record actual addresses rather than reference addresses, repeat with a changed byte count, and explain the limits of the ASLR conclusion. Keep analysis.md and trace.md as separate deliverables.
