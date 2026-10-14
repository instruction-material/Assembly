# Optional runtime control-flow investigation

Complete this after analysis.md. Use the same program and a separate saved worksheet.

1. TODO BUILDS: Identify the exact baseline and guard-pie binaries and record their static ELF evidence.
2. TODO POLICY: Record GDB version, disable-randomization setting and any runtime restrictions without changing system policy.
3. TODO ENTRY: Break at checksum_c and checksum_asm with the default input. Record actual entry addresses, RDI, RSI, RSP and the next instruction. RSI should describe eight bytes.
4. TODO FLOW: Step real instructions and connect one guarded C control-flow path and the handwritten loop to their disassembly. Record what was executed rather than only what could execute.
5. TODO RETURNS: Record both observed returns and the final match result. Repeat with ABC or empty input and explain the changed count and path.
6. TODO CLAIM: Explain what the observations establish and why neither differing nor repeated addresses alone proves the system's ASLR policy.
