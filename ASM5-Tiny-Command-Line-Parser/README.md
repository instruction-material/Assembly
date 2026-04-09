# ASM5 Tiny Command-Line Parser

Parse decimal arguments and dispatch a small command in a mixed C and assembly
CLI.

## Goals

- inspect `argc` and `argv` in a debugger
- compare command names with an assembly string routine
- parse decimal text into signed integers

## Starter Expectations

- extend the decimal parser so it handles more input cases
- explain each parse-state transition on paper
- run the parser with several short command examples

## Solution Highlights

- supports command-name equality checks
- parses signed decimal integers in assembly
- drives a tiny `sum`, `max`, or `xor` command path
