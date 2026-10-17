# Control-flow observations

Record the target, selected role, compiler/version, build type and commands.
Keep the original prediction and untouched failure beside the minimal repair.

| Current PC / instruction | Relevant registers before | Current CMP flags | Chosen successor PC | Registers after | Explanation |
| --- | --- | --- | --- | --- | --- |

For dispatch, predict the selected case, visited-case mask, comparison count
and result for all four selectors. Trace the path into the selected label,
through its exit and into the shared join. Explain the untouched fall-through
using actual current PCs. Case labels do not themselves change control flow.

For the loop, state the invariant at lab_check and record count, index, sum,
body visits and visited-index mask before each decision. Include zero, one and
fifteen iterations. Explain the equality boundary using the immediately
preceding CMP, then distinguish body visits from the exit index.

Retain default and --changed runs, Debug/Release checks with GCC and Clang,
one independently chosen boundary pair, and a rejected copied regression.
Keep main.c, lab.h, model.c, tests.c and abi_checks.S unchanged. A passing
contract does not supply the current addresses or complete this table.
