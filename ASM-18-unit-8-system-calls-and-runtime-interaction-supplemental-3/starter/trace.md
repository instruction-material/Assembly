# Syscall evidence worksheet

## Prediction
Record the function arguments, syscall number, kernel argument registers and
the distinction between a raw negative return and libc errno conversion.

## Observation
Record target, compiler, build profile, source role, command and exit status.
Capture the actual SYSCALL entry registers, return value and next instruction.
Keep the original unfinished result and the completed result in separate rows.

## Changed case
Record the changed payload or requested mode, actual transferred bytes or file
permissions, the observed errors and the reason the caller stops or continues.

## Ownership and cleanup
Identify only descriptors and temporary paths created by this process. Record
their close/unlink/rmdir evidence; distinguish a full pipe from a failed syscall.

## Explanation
Connect the observed kernel boundary to the C function ABI and libc wrapper.
Explain the controlled regression and why a passing build alone is insufficient.
