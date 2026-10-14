# Compiler-output analysis reference

This reference explains the portable parts of the analysis. The required record still uses actual compiler version, commands and observed instruction addresses from the local Linux x86-64 build. No fixed compiler listing or address is an answer for every environment.

## Predictions and machine contract

The operation is the low 64 bits of value*factor+bias, interpreted as signed. The four default outputs are 37, -26, 5 and -9223372036854775808. INT64_MAX*2+7 wraps to bit pattern 5. INT64_MIN*(-1) retains the minimum bit pattern modulo 2^64.

Under this integer System V signature, value starts in RDI, factor in RSI and bias in RDX; the final result returns in RAX. RBX, RBP and R12 through R15 remain preserved. The actual compiler may move those values into other registers or stack slots after entry.

## Source to actual instructions

The unsigned multiplication and addition retain the low word. A signed or unsigned multiply instruction can produce that same low word; the mnemonic alone does not identify the C type. memcpy copies the representation rather than using a potentially out-of-range signed conversion. Optimized code can implement that copy entirely in registers.

A typical unoptimized listing exposes local stack storage and more moves. A typical optimized listing holds intermediates in registers and avoids unnecessary copies. Record the actual listings: instruction selection, register allocation, prologues and debug locations depend on compiler/version/flags. Directives, comments and labels are not executable instructions.

## Changed case

One example is value=4294967296, factor=4294967296, bias=1. The product wraps from 2^64 to zero, leaving result 1. This detects a full-width modular interpretation that small examples cannot establish. The unchanged contracts and independent Python oracle cover 10,013 fixed/deterministic triplets per profile and six preserved registers.

## Trace and conclusion

At the first instruction of compiled_score in the default driver, the argument registers contain 6, 7 and -5. The return is 37. Step the actual instructions and relate register/stack changes to the C expression; -O2 source-line steps may cover several source statements at once.

The two optimization levels preserve observed results in the checked cases while changing their instruction representation. A shorter listing alone does not establish a faster program, a timing guarantee or exhaustive correctness across 2^192 triplets. Timing and workload design belong to the later performance lab.
