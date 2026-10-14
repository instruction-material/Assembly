# Instruction-level fault and repair reference

The deliberate fault revisits the earlier array-search idea for a different
purpose: locate the first incorrect machine-state transition and prove the
same trace after a minimal repair. It is not another search-implementation
assignment.

For {-8,-1,4}, the first signed nonnegative value is at index 2. The faulty
branch returns index 0. At the first decision, R8D holds 0xfffffff8, signed
-8, and RCX is 0. CMP R8D,0 gives SF=1, OF=0, ZF=0 and CF=0. JAE tests CF=0
and therefore follows debug_found even though the signed value is negative.
The load and flags are valid; that branch is the first wrong transition.

The corrected JGE uses SF==OF, so this comparison falls through debug_advance.
The next negative value also fails the signed condition; 4 reaches the
found path and returns 2 in RAX. Record the actual compiler, command,
addresses and before/after trace from the current build; no fixed address
is a universal debugger answer.

A changed case {-8,0,4} must return 1. Zero satisfies >=0, so a strict JG
repair is also wrong. Predict 1 before changing the demo array and expected
constant, then repeat the trace and keep the untouched contracts passing.

Count<=0 returns -1 without accessing values, including a null pointer.
Positive counts require that many readable int32_t entries. The function
does not write input, reads only indices below count and preserves all six
callee-saved registers. Contract success is bounded execution evidence;
the worksheet still requires the saved fault/repair comparison and new case.
