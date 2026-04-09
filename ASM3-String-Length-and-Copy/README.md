# ASM3 String Length and Copy

Implement classic string-walking routines in assembly.

## Goals

- practice byte loads and stores
- reason about null termination and buffer capacity
- connect pointer movement to visible string output

## Starter Expectations

- improve the bounded copy behavior
- explain when the loop stops for `strlen` and for copying
- show what bytes land in the destination buffer after truncation

## Solution Highlights

- computes string length byte by byte
- performs a `strlcpy`-style bounded copy
- preserves a stable null terminator when capacity is available
