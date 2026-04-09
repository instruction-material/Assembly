# ASM4 Call a C Helper from Assembly

Call back into a C helper while preserving ABI rules.

## Goals

- practice mixed C and assembly builds
- keep argument registers and preserved registers straight
- understand why stack alignment matters before a call

## Starter Expectations

- add the actual helper call from assembly
- explain how the arguments are repacked for the helper
- verify that the final result is clamped correctly

## Solution Highlights

- sums and scales values in assembly
- calls a C clamp helper with a valid calling-convention setup
- shows one small, practical mixed-language workflow
