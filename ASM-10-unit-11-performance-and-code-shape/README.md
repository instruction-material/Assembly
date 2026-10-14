# Performance and Code Shape: Correctness Before Timing

This Linux x86-64 System V project compares real assembly loops over the same data. Both starter and reference programs already work. The required learner artifact is `analysis.md`: predictions, actual measurements, code-shape observations, a changed fixture and a bounded conclusion. Passing code tests does not complete that analysis.

## Target, files and contract

Use Linux x86-64, CMake 3.20+, Clang or GCC, GDB and objdump. Use an x86-64 Linux VM/lab on macOS or an x86-64 WSL distribution on Windows. The programs use C17 and GNU-style assembly in Intel syntax. Assembly is exported and built natively; the website IDE edits/saves the selected role rather than executing Linux assembly in the browser.

- `loops.S` contains three complete routines.
- `performance.h` declares their exact interfaces.
- `dataset.c` generates reproducible fixtures and supplies an unsigned C comparison.
- `main.c` verifies checksums, warms the variants and emits actual timing CSV.
- `tests.c` checks full-width results, bounded/read-only memory, repeated indices and nonpositive counts.
- `abi_checks.S` checks preservation of RBX, RBP and R12–R15 with aligned calls.
- `CMakeLists.txt` configures the native role build.
- `analysis.md` records the required evidence. The reference supplies reasoning, not portable timing numbers.

`sum_nonnegative_branch(values, count)` and `sum_nonnegative_cmov(values, count)` return the sum of signed `int64_t` elements greater than or equal to zero, as `uint64_t` bits modulo 2^64. For `count <= 0` they return zero without reading memory; NULL is allowed then. A positive count requires that many readable elements. Arrays are read-only and no element outside the declared range may be accessed.

`sum_nonnegative_indexed(values, indices, count)` applies the same rule to the selected elements. Positive counts require readable arrays of at least `count` entries, and every index must be less than `count`. Repeated indices are permitted and count as repeated visits. The benchmark uses permutations, so its indexed variants have the same sum as sequential traversal; arbitrary repeated-index calls need not. All routines preserve the System V callee-saved registers.

The example `[-3, 0, 5, INT64_MAX, INT64_MAX]` has result 3 modulo 2^64. Explain that wraparound before running it. Changing `>= 0` to `> 0` cannot change this sum because zero contributes zero, although a differently placed branch can alter observed control flow.

## Build and verify a role

Run these commands from this project folder, whose children are `starter/` and `solution/`:

```sh
cmake -S starter -B build-starter-debug -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_C_FLAGS_DEBUG="-O0 -g"
cmake --build build-starter-debug
ctest --test-dir build-starter-debug --output-on-failure
./build-starter-debug/assembly_performance --example

cmake -S starter -B build-starter-release -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang -DCMAKE_C_FLAGS_RELEASE="-O2 -g -DNDEBUG"
cmake --build build-starter-release
ctest --test-dir build-starter-release --output-on-failure
./build-starter-release/assembly_performance --example
```

Expected example output is `branch=3 cmov=3 indexed=3 expected=3`. Both roles pass the unchanged contracts initially. Use separate build directories for the reference or GCC. The handwritten assembly is unchanged by the C optimization flags; build mode also changes the surrounding C harness.

If an exported workspace puts the selected role directly at its root, replace `-S starter` with `-S .`. Do not silently mix the project-folder and selected-role layouts. Keep earlier attempts before consulting the reference.

## Fixtures and comparisons

Three fixtures are generated from a documented unsigned 64-bit LCG, with arithmetic modulo 2^64:

```text
state = state * 6364136223846793005 + 1442695040888963407
seed = 0x814fa27065b39c12 + pattern_number
```

Pattern numbers 0, 1 and 2 mean nonnegative, alternating and seeded-mixed. Nonnegative values clear bit 63. Alternating values use that magnitude at even indices and `-magnitude-1` at odd indices. Mixed values use the generated 64-bit signed representation. Identity indices visit `0..count-1`; a seeded Fisher–Yates permutation uses subsequent LCG states and `state % remaining` for each swap. The resulting order is reproducible, not a claim of cryptographic or perfect statistical randomness.

Four variants use that fixture: branch-sequential, cmov-sequential, indexed-identity and indexed-permuted. Compare branch and conditional-move versions on the same signed values. Conditional move removes the value-dependent jump here, but loop control and the harness still branch.

For locality, first compare indexed-identity and indexed-permuted on the **nonnegative** pattern: the indexed instruction body and eligibility outcome are the same, while the data access order changes. On alternating/mixed values the permutation also changes the sequence of branch outcomes. Report that confounding factor; those timings do not isolate cache behavior. Comparing sequential versus indexed traversal additionally introduces index loads and address calculation.

## Measure and retain observations

```sh
./build-starter-release/assembly_performance --benchmark > release-default.csv
./build-starter-release/assembly_performance --benchmark 64 3 2 > release-small.csv
./build-starter-debug/assembly_performance --benchmark > debug-default.csv
clang --version
uname -a
lscpu
```

Each command must exit successfully. A failure can leave a partial CSV, which is not accepted evidence. Defaults are count 4096, repeats 32 and trials 5: three patterns, four variants and five trials yield 60 data rows. The changed run above yields 24. Count must be a power of two from 64 through 1,048,576, repeats 1–1024 and trials 1–21; the product `count * repeats * trials * 12` is capped at two billion element visits.

`elapsed_ns` is real elapsed time from two `clock_gettime(CLOCK_MONOTONIC)` calls. Its nanosecond unit is not a promise of nanosecond precision. Successive clock values can be equal. This clock avoids discontinuous wall-clock changes, but timing can still reflect clock adjustment, scheduling, contention, cache state and the machine. See the [Linux man-pages clock_gettime reference](https://man7.org/linux/man-pages/man2/clock_gettime.2.html).

Before timing each pattern, all variants must match the unsigned C sum; they are then warmed. Trial `t` rotates the starting variant by `t % 4`. Timed calls accumulate a modulo-2^64 checksum, retained through a volatile sink. Every row must match `expected_checksum = fixture_sum * repeats modulo 2^64`. The elapsed interval includes dispatch, calls, loop work and checksum accumulation, so it is not an isolated instruction latency.

Save the raw CSV, compiler version, exact flags, CPU/OS, available cache information and relevant machine load. Compare repeated results for the same pattern/count/build first. Calculate a median and range for each variant; show all trials rather than selecting the fastest observation. Change the count to explore working-set size, with correctness checks repeated before timing. No required speed ratio, elapsed threshold or universal winner is specified.

## Connect machine state to code shape

From the project folder:

```sh
objdump -d -M intel build-starter-release/assembly_performance > release-disassembly.txt
gdb -q build-starter-debug/assembly_performance
```

Inside GDB:

```text
set disassembly-flavor intel
tbreak *performance_branch_decision
run --example
info registers rax rcx r8 eflags
x/i $pc
si
x/i $pc
finish
print /u $rax
```

At the first decision the value is -3 and index is zero. The signed value test sets SF=1, OF=0, ZF=0 and CF=0; `jns` is not taken. The next instruction advances the index. Record the instruction address, value before and after the instruction, flags and evidence for the branch. The final returned bits are 3. Compare the real branch, conditional-move and indexed function bodies; do not infer time solely from static instruction counts or assume every instruction has one fixed cost.

## Required analysis and guided sequence

1. Confirm the architecture/ABI/tool versions and predict the example's modulo sum.
2. Pass Debug and Release contracts before comparing any times.
3. Retain both default and changed-count CSV, all trial rows and machine context.
4. Compare branch outcomes on the three signed patterns; use the nonnegative indexed pair for the cleaner access-order comparison.
5. Relate measured differences to actual instructions, including remaining branches, extra index loads and harness cost.
6. Save the instruction-step table and one predicted changed case. For example, changing 5 to 6 in the demonstration gives result 4; update only that demonstration's predicted expectation and keep the function contracts unchanged.
7. Write a limited conclusion, name confounders and propose a repeat or changed-size run that could test the explanation.

A guided session walks through the same sequence and evidence as independent study. The reference worksheet explains the invariants and analysis method; its reasoning does not complete another machine's observation table. Correctness, reproducibility and supported interpretation are the completion criteria.
