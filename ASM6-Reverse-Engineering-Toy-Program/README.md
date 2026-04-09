# ASM6 Reverse-Engineering Toy Program

Recover high-level logic from a hand-written assembly routine.

## Goals

- read a short assembly function without starting from source
- reconstruct equivalent pseudocode or C
- compare the original routine and the reconstructed logic on sample inputs

## Starter Expectations

- inspect the `mystery` routine before editing the reconstruction
- identify the absolute-value path, parity branch, and final threshold branch
- finish the reconstructed logic in C

## Solution Highlights

- keeps the mystery routine small but branchy
- demonstrates a repeatable reverse-engineering workflow
- compares original and reconstructed outputs side by side
