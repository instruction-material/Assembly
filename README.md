# Assembly

Source material for the Assembly course, centered on Linux x86-64 and the System V AMD64 ABI. Use the project guide for the exact target, compiler, tasks and completion contract.

## Project sequence

0. `ASM-04-asm0-setup-and-tooling`: build and trace a mixed C/assembly function.
1. `ASM1-Integer-Calculator`: signed 64-bit arithmetic, division and bitwise operations.
2. `ASM2-Array-Sum-and-Search`: bounded array walks and signed first-match search.
3. `ASM3-String-Length-and-Copy`: byte walks and bounded string copying.
4. `ASM4-Call-C-Helper-from-Assembly`: calls across the C/assembly boundary.
5. `ASM5-Tiny-Command-Line-Parser`: process arguments and runtime interaction.
6. `ASM6-Reverse-Engineering-Toy-Program`: recover the behavior of a course-owned routine.

Each project has a learner `starter/`, a reference `solution/`, and a `README.md`. Select the learner role first. The additional `ASM-` folders support unit practice and optional studios; select them according to the site course's learning path.

## Native setup

For the opening function, calculator and array projects, use Linux x86-64, CMake 3.20 or later, Clang or GCC, and GDB. Their role folders contain independent CMake builds and tests. On macOS, use an x86-64 Linux VM or lab; on Windows, use an x86-64 WSL distribution.

Example from a project folder:

```sh
cmake -S starter -B build-starter -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-starter
ctest --test-dir build-starter --output-on-failure
```

An unfinished starter is expected to fail its completion checks. Follow the project guide to complete the named task, predict the output, and repeat the same tests. Build the reference in a separate folder and repeat both with Release and GCC.

## Collection build and validation

The root `CMakeLists.txt` builds the original six-project collection with Clang:

```sh
cmake -S . -B build
cmake --build build
```

Collection binaries are under `build/bin/`. Use each project's independent role build for its completion contracts. The native CI workflow exercises the opening function, calculator and array verifiers with both compilers and real GDB traces. Further project contracts are added as their course audit is completed.

## Learning sequence

Read the target and function contract, predict a small example, edit the named learner task, run the unchanged tests, and record an instruction-level trace. Explain arguments, widths, addresses, flags, branches and the return value. Use the reference to review an already tested attempt and choose optional practice according to the next learning goal.
