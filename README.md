# Assembly

This folder is structured as the future `instruction-material/Assembly`
repository.

The materials follow the main project sequence used by the site course:

1. `ASM1-Integer-Calculator`
2. `ASM2-Array-Sum-and-Search`
3. `ASM3-String-Length-and-Copy`
4. `ASM4-Call-C-Helper-from-Assembly`
5. `ASM5-Tiny-Command-Line-Parser`
6. `ASM6-Reverse-Engineering-Toy-Program`

Each project contains:

- `starter/` with a guided scaffold and one or more intentionally incomplete
  routines
- `solution/` with a complete reference implementation
- `README.md` explaining the low-level goal of the lab

## Tooling

Preferred IDEs:

- `CLion`
- `VS Code`

Expected local toolchain:

- `clang`
- `cmake`
- `lldb`

The projects standardize on small mixed `C` plus `x86-64 assembly` binaries so
students can focus on registers, stack frames, and calling conventions without
also carrying a large runtime or framework.

## Apple Silicon Note

This pack targets `x86_64` on purpose. On Apple Silicon, the CMake file forces
`x86_64` binaries so the labs can be run through Rosetta with:

`arch -x86_64 ./build/bin/<binary-name>`

## Local Validation Workflow

From this folder:

1. `cmake -S . -B build`
2. `cmake --build build`
3. Run the generated starter or solution binaries from `build/bin/`

## Teaching Notes

- start from reading before writing
- keep register traces beside the code
- use mixed C and assembly views frequently
- prefer tiny routines that can be stepped instruction by instruction
