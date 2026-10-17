# Pointer Aliasing and Reload Decisions: observations

## TARGET

TODO TARGET: Record uname -s, uname -m, compiler --version, the complete flags and the selected role. Explain why baseline.c and operation.c are built separately without LTO.

## PREDICT

TODO PREDICT: Predict all five default and changed words, then the additional cases in README.md. Keep these predictions separate from observed output.

## TYPES

TODO TYPES: Explain the exact C values, types, access widths and valid input/pointer domain before mapping any instructions.

## MAP

TODO MAP: Generate both baseline.s listings and linked disassembly. Map each inspected helper to its real argument operands, operations and return value.

## OPTIMIZE

TODO OPTIMIZE: Compare the same compiler at -O0 and -O2 with other flags fixed. Identify actual changes and one behavior the optimization must preserve.

## TRACE

TODO TRACE: Retain real entry/return PCs, argument widths, RSP, caller return word and instruction steps at both levels. Include actual owned-memory changes for pointers.

## REGRESSION

TODO REGRESSION: In a separate reference copy apply only the documented changed body. Retain the rejected case and an agreeing case, then restore the supplied source.
