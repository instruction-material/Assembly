# Pointer Aliasing and Reload Decisions: observations

## TARGET

The role is C17 on ordinary-user Linux x86-64 with eight-byte uint64_t objects and the System V AMD64 ABI. CMake builds baseline.c and operation.c separately without LTO. This keeps the inspected helper calls available while their bodies optimize. Record the actual target, compiler version and all flags using README.md; do not copy instruction addresses from another run.

## PREDICT

Default3,5 makes the ordinary arguments point to the same slot. The conceptual updates are3+5=8 and8 XOR8=0; the second slot stays5. The separate restricted call produces left8 and right13. Outputs are0,0,5,8,13. Changed2,5 uses distinct ordinary slots and yields7,7,2,7,2. Initial UINT64_MAX with incoming1 wraps the addition to0; as the initial is odd, the ordinary result is0 and untouched second slot1. Zero inputs give five zero words. The UINT64_MAX,1 case gives 0,0,1,0,1. Odd initial3 with incoming0 gives 0,0,0,3,3.

## TYPES

Each helper receives two valid uint64_t pointers and an unsigned delta. operation.c owns both arrays and fixes every pointer to one of their two slots. Ordinary calls support equal or distinct pointers. The restricted call always uses separate modified objects; an equal-pointer call would violate this task's access contract and is never executed. Unsigned addition and XOR have defined full-width behavior. Restrict does not insert a runtime test.

## MAP

Locate compiled_plain and compiled_restricted in actual generated and linked output. RDI/RSI hold the two object addresses and RDX the unsigned delta; RAX returns a full uint64_t. Follow actual eight-byte reads and stores, preserving whether the two addresses are equal. The ordinary return observes the final left object after the right store. A compiler may retain a value under the restricted contract, but the observed generated code decides whether it did so.

## OPTIMIZE

At -O0 there may be stack-spilled pointers and temporary values. At -O2 an ordinary helper must still work when its two pointers alias, whereas the restricted helper can rely on its caller obligation. Inspect actual reloads after the right store and any reordered stores. Intermediate nonvolatile memory operations need not correspond one-to-one with C source lines. The valid outputs, access domain and ABI remain the same; neither a specific reload count nor a speedup is guaranteed.

## TRACE

For the default ordinary call, record equal addresses and initial words3,3. Step its real instruction sequence and retain every selected owned-word state; final words and return are0. For the restricted call, record distinct addresses and initial3,5; final words are8,13 and return8. Verify both actual RET destinations and restored caller stack positions. Repeat on -O2 with fresh addresses. Sanitizer success cannot establish that every future caller respects restrict.

## REGRESSION

The cached-return replacement computes8 for the default, stores through the aliased right pointer to make the object0, then incorrectly returns the cached8. The unchanged contracts and default reject this defined-but-wrong body. Changed2,5 still returns7 and therefore cannot detect it. Keep both cases, the independent model and the restricted helper unchanged. Restore the supplied ordinary body after the disposable comparison.
