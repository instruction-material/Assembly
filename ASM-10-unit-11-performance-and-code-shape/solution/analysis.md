# Reference reasoning and observation method

## TARGET
The target is Linux x86-64 with the System V AMD64 ABI and C17. Record the actual compiler, exact Debug/Release flags, CPU/OS/cache information and relevant load for the run being analyzed. Timings from a different machine cannot fill the observation table.

## PREDICT
The negative -3 is omitted and zero contributes zero. Eligible values sum to 5 + 2*(2^63-1) = 2^64+3, so the returned uint64_t bits are 3. Nonpositive counts return zero without a read; positive counts require readable arrays. Every indexed position is bounded by count. Repeated indices repeat a contribution, so only permutations guarantee equality with sequential traversal.

## CORRECT
Both role programs are working baselines. Preserve successful Debug/Release contracts and the example output. For a fixed benchmark pattern, all four variants have the same fixture sum because both index orders are permutations. A row's accumulated checksum is fixture_sum * repeats modulo 2^64. Reject partial output from a failing process.

## MEASURE
Insert the actual raw CSV and compiler/machine context, including the default count=4096, repeats=32, trials=5 and a changed-count run such as 64/3/2. Each default run has 60 rows; the changed run has 24. Group by pattern, variant, count and build, then retain every trial and compute median and range. There is no reference elapsed value or universal winner. Warmup and rotation reduce some order effects but do not remove scheduling, contention or thermal/caching variability.

## MAP
The branch loop tests a signed 64-bit value and conditionally adds it. The conditional-move loop selects either that value or zero, but retains its loop-control jump. The indexed loop additionally loads an index and uses a scaled data address. For the first example decision, RCX=0 and R8=-3; SF=1, OF=0, ZF=0, CF=0, so jns falls through to increment the index. Retain actual instruction addresses and before/after values from the run. Static instruction counts alone do not establish elapsed cost.

## CASE
Changing the demonstration's 5 to 6 predicts result 4 modulo 2^64. Change the demonstration expectation consistently after writing that prediction, while leaving the general routine contracts and tests intact. A changed count changes the generated fixture and working-set size; verify its own checksums rather than reusing the default fixture sum.

## EXPLAIN
Compare indexed identity and permutation on nonnegative values first: the instruction body and eligibility branch outcome are held constant while access order changes. Mixed or alternating patterns also change the sequence of branch outcomes when permuted, so their indexed difference does not isolate locality. Sequential versus indexed comparison adds index loads/address work. Debug/Release also change the C harness around unchanged handwritten assembly. Elapsed intervals include dispatch, calls and accumulation, not isolated instruction latency. State only what the actual repeated measurements support, list uncertainty and repeat under another count or condition before generalizing.
