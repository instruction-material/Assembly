# Instruction-level fault and repair record

The supplied starter builds, but its signed-comparison behavior is wrong.
Record the failing trace before changing routine.S. Passing tests after a
repair does not complete the evidence below.

## Target and reproducible failure
TODO TARGET: Record OS, architecture, compiler/version, flags and commands.
TODO FAILURE: Predict the first nonnegative index for {-8,-1,4}; record the
observed demo result, exit status and first failing contract.

## First incorrect state transition
TODO BEFORE: At debug_branch_decision, record the actual instruction address,
pointer/array values, RCX, signed R8D and SF/OF/ZF/CF before the branch.
TODO AFTER: Single-step once; record the next address/instruction and explain
why this is the first incorrect transition, rather than a bad memory load.

## Small repair and repeated proof
TODO REPAIR: Describe the branch condition, make the smallest correction in
routine.S and repeat the same breakpoint/flags/step/return trace.
TODO CASE: Predict a changed zero-containing case before running; edit the
demo array and expected index together, then retain passing contracts.
TODO EXPLAIN: Explain signed versus unsigned branch conditions, count<=0
without memory access, bounds, preserved registers and evidence limits.
