# Byte Promotions and Signed Comparisons: observations

## TARGET

The target is ordinary-user Linux x86-64 and the System V AMD64 ABI. The header requires eight-bit exact-width byte types and a 32-bit int. The CMake role build sets C17 and disables interprocedural optimization. Separate translation units preserve calls to the two inspected helpers while allowing their bodies to optimize. Use the exact commands in README.md and retain the current compiler version; the reference does not supply another machine's addresses.

## PREDICT

Default index7 selects byte80: signed -128, unsigned128, threshold0. The five words are 0000000000000007 ffffffffffffff80 0000000000000080 0000000000000001 0000000000000000. Zero inputs select byte0 and threshold -128, giving five zero words. At threshold -1, signed/unsigned results for 7f,80,ff are (0,0),(1,0),(0,0). At threshold0 they are (0,0),(1,0),(1,0); at127 they are (0,0),(1,0),(1,0). Equality uses strict less-than, so signed -1 is not less than -1.

## TYPES

The helper parameters are int8_t/int and uint8_t/int. The byte operands promote to int, preserving their respective values. The full int range includes every uint8_t value. Thus the unsigned byte's comparison can still use a signed int condition. memcpy transfers one valid byte representation into int8_t; the signed output is then converted to uint64_t modulo 2^64. The masked index bounds the shift to0..56 and the threshold stays in -128..127.

## MAP

Locate compiled_signed_compare and compiled_unsigned_compare in actual baseline-O0.s/baseline-O2.s and the linked listing. Their first arguments use only the low byte of the integer argument register; the threshold is an int, and the return is an int boolean in EAX. Upper argument-register bits are not the byte value contract. Find actual sign/zero extensions and compare operands before interpreting branch or SETcc mnemonics. Generated directives and debug records are not executed operations.

## OPTIMIZE

A build may remove the frame and stack-spilled parameters, keeping the widened byte and threshold in registers. The signed-byte value remains negative for80..ff; the unsigned-byte value remains0..255. The true/false results and five-word output must remain equal at both levels. An opcode or shorter instruction count is not a C guarantee. Compare the two listings from the same compiler, then repeat separately with GCC or Clang.

## TRACE

For the default, break at each helper entry. Record the actual low argument byte80 and int threshold0. Step the current instructions through RET: signed comparison returns int1, unsigned comparison int0. Check only the declared int return width, and verify actual caller PC/RSP against the saved entry return word and stack. Repeat with the optimized executable and retain its own addresses and sequence.

## REGRESSION

Changing only the signed helper to return (uint8_t)value < threshold gives false for signed -128 versus0, although the supplied contract requires true. The default and unchanged contracts reject it. Zero inputs still agree because0 is not below -128. A second counterexample is signed -1 versus0. The controlled cast is defined C; its changed meaning is the error, not undefined behavior.
