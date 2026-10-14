# Performance observations

## TARGET
TODO TARGET: record Linux x86-64/System V, compiler version, exact flags, CPU/OS/cache information and machine context.

## PREDICT
TODO PREDICT: derive the result 3 for [-3, 0, 5, INT64_MAX, INT64_MAX] modulo 2^64. State the valid-count and bounded-index contracts, including repeated visits.

## CORRECT
TODO CORRECT: retain successful Debug and Release contracts, example output and matching checksums before timing. Code tests do not complete this worksheet.

## MEASURE
TODO MEASURE: retain raw CSV for the default and changed-count runs. Record all trials, rotating order, median and range for every pattern/variant/build. Insert actual elapsed observations; no target speed is supplied.

## MAP
TODO MAP: identify value-dependent jumps, conditional move, loop control, index loads and address calculations in the actual disassembly. Record one instruction address, value before, value after, flags and evidence for its next step.

## CASE
TODO CASE: predict and verify an additional demonstration or count. Keep the function contract unchanged and explain modulo wraparound.

## EXPLAIN
TODO EXPLAIN: use the nonnegative indexed pair for the cleaner access-order comparison. Name the mixed-pattern branch-order confounder, harness cost and machine variability. State a bounded conclusion and a repeat that could challenge it.
