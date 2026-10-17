# Stack observations

Record the selected role, platform, compiler/version, build type and commands.
Keep predictions, the untouched observation and the minimal repair separately.

| Current PC and instruction | RSP before/after | Owned stack slots | Registers before/after | Next PC and reason |
| --- | --- | --- | --- | --- |

For LIFO, name the original return-address slot and both newly pushed slots.
Predict which value each POP receives. Record RSP at lab_operation, lab_pops,
lab_restored and lab_return; distinguish a correct stack height from a correct
value order. Explain why the original return address is still the top word at
lab_return, and step RET to verify the caller resumes there.

For the nested call, draw the 24-byte local frame and its three owned slots.
Record RSP modulo 16 before CALL and at lab_helper. Show the actual return
address pushed by CALL and compare it to lab_after_call. Step the helper RET,
observe the restored caller PC and RSP, and trace both local-value reloads.
Record which argument registers the helper deliberately clears. Explain why
the frame remains allocated until all three local slots have been read.

Retain default/--changed runs, GCC and Clang Debug/Release contracts, an
independently predicted unequal boundary pair, and a copied rejected
regression. Equal inputs conceal the named mistakes; explain that limitation.
Keep main.c, lab.h, model.c, tests.c and abi_checks.S unchanged. Passing a
contract does not complete this address/stack trace.
