"""Observe actual owned bytes, access widths, LEA values, flags and GDB steps."""
import argparse
import ast
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

PACKS = {"memory": "ASM-03-unit-1-machine-model-and-toolchain-supplemental-2",
         "lea": "ASM-04-unit-1-machine-model-and-toolchain-supplemental-3"}
ROLE_FILES = ("routine.S", "main.c", "lab.h", "model.c", "tests.c", "abi_checks.S", "CMakeLists.txt", "trace.md")
MASK = (1 << 64) - 1
FIXED = [0, 1, 2, 31, 32, 63, 64, 65, 127, 128, 255, 9223372036854775807, 9223372036854775808, 9223372036854775809, 12297829382473034410, 18446744073709551615]


def model(mode, initial, incoming):
    if mode == "memory":
        data = initial.to_bytes(8, "little") + incoming.to_bytes(8, "little")
        return [int.from_bytes(data[offset:offset+width], "little") for offset, width in ((0,1),(1,2),(4,4),(0,8),(3,8),(8,8))]
    return [(initial + incoming) & MASK, (initial + incoming * 2) & MASK, (initial + incoming * 4 + 13) & MASK, (initial + incoming * 8 - 7) & MASK, (incoming * 8) & MASK]


def demo_inputs(mode, changed):
    if mode == "memory":
        return (0x80000000000000ff, 1) if changed else (0x0102030405060708, 0xf1e2d3c4b5a69788)
    return (0xfffffffffffffff0, 0xffffffffffffffff) if changed else (0x1000, 3)


def compare_flags(left, right):
    result = (left - right) & MASK
    overflow = (((left ^ right) & (left ^ result)) >> 63) & 1
    return int(left < right) | (int(result == 0) << 6) | (((result >> 63) & 1) << 7) | (overflow << 11)


def cases():
    result = [(initial, incoming) for initial in FIXED for incoming in FIXED]
    state = 0xdecafbad87912345
    for _ in range(10013):
        state = (state * 6364136223846793005 + 1442695040888963407) & MASK
        initial = state
        state = (state * 6364136223846793005 + 1442695040888963407) & MASK
        result.append((initial, state))
    assert len(result) == 10269
    return result


ORACLE_DRIVER = '''#include "lab.h"
#include <inttypes.h>
#include <stdio.h>
int main(void) {
    uint64_t initial, incoming;
    while (scanf("%" SCNx64 " %" SCNx64, &initial, &incoming) == 2) {
        LabResult output = {0};
        int preserved = 0;
        abi_probe(lab_operation, initial, incoming, &output, &preserved);
        printf("%d", preserved);
        for (size_t field = 0; field < LAB_FIELD_COUNT; ++field)
            printf(" %016" PRIx64, output.value[field]);
        putchar('\\n');
    }
    return feof(stdin) ? 0 : 64;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", choices=("clang", "gcc"), required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    ast.parse(Path(__file__).read_text(), feature_version=(3, 10))
    sources = {}
    for pack in PACKS.values():
        assert [name for name in ROLE_FILES if (root / pack / "starter" / name).read_bytes() != (root / pack / "solution" / name).read_bytes()] == ["routine.S"]
        for name in ["README.md"] + [role + "/" + name for role in ("starter", "solution") for name in ROLE_FILES]:
            raw = (root / pack / name).read_bytes()
            assert raw
            sources[pack + "/" + name] = hashlib.sha256(raw).hexdigest()
    assert len(sources) == 34
    args.proof = args.proof.resolve()
    args.proof.parent.mkdir(parents=True, exist_ok=True)
    proof = {"compiler": args.cc, "sourceFiles": sources, "nativeExecuted": False, "profiles": [], "debuggerTraces": [], "inputRefusals": []}
    if args.source_only:
        args.proof.write_text(json.dumps(proof, indent=2) + "\n")
        print("34 source files and Python 3.10 syntax accepted; native programs not executed")
        return
    assert sys.platform == "linux" and platform.machine().lower() in ("amd64", "x86_64")
    assert os.geteuid() != 0, "Use an ordinary-user native lab"
    cc = shutil.which(args.cc)
    assert cc and all(shutil.which(name) for name in ("cmake", "ctest", "gdb", "objdump", "readelf"))
    work = args.proof.parent / ("machine-" + args.cc + "-observations")
    work.mkdir(exist_ok=False)
    records = []

    def run(argv, directory, label, expected=0, stdin=None, timeout=120):
        child = subprocess.Popen(argv, cwd=directory, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        record = {"parentTask": "assembly-machine-native", "parentPid": os.getpid(), "pid": child.pid,
                  "cwd": str(directory), "command": argv, "startTime": time.time(), "timeoutSeconds": timeout}
        if stdin is not None:
            record.update(stdinSha256=hashlib.sha256(stdin).hexdigest(), stdinBytes=len(stdin))
            (directory / (label + ".stdin.txt")).write_bytes(stdin)
        logs = args.proof.with_suffix(".processes.jsonl")
        with logs.open("a") as stream: stream.write(json.dumps(dict(record, event="start")) + "\n")
        cleanup = "process exited"
        try:
            out, err = child.communicate(input=stdin, timeout=timeout)
        except BaseException:
            try: os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: out, err = child.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                out, err = child.communicate()
            cleanup = "owned process group terminated and reaped"
            raise
        finally:
            record.update(endTime=time.time(), exitCode=child.returncode, childProcessGroupCleanup=cleanup)
            with logs.open("a") as stream: stream.write(json.dumps(dict(record, event="end")) + "\n")
        (directory / (label + ".stdout.txt")).write_bytes(out)
        (directory / (label + ".stderr.txt")).write_bytes(err)
        records.append(record)
        assert child.returncode == expected if expected is not None else child.returncode != 0, (label, child.returncode, err.decode(errors="replace"))
        return out.decode(), err.decode()

    version, _ = run([cc, "--version"], work, "compiler-version")
    proof["compilerVersion"] = version
    inputs = cases()
    payload = "".join(f"{initial:016x} {incoming:016x}\n" for initial, incoming in inputs).encode()
    for mode, pack in PACKS.items():
        for label, role, build_type in [("untouched", "starter", "Debug"), ("completed", "starter", "Debug"),
                                        ("reference", "solution", "Debug"), ("release", "solution", "Release"),
                                        ("wrong-operation", "solution", "Release"), ("preserved-register", "solution", "Debug")]:
            directory = work / (mode + "-" + label)
            shutil.copytree(root / pack / role, directory)
            routine = directory / "routine.S"
            if label == "completed": routine.write_bytes((root / pack / "solution/routine.S").read_bytes())
            elif label == "wrong-operation":
                before, after = ("    mov rax, QWORD PTR [rsp + 0]\n", "    mov rax, QWORD PTR [rsp + 0]\n    bswap rax\n") if mode == "memory" else ("    lea rax, [rdi + rsi*8 - 7]\n", "    lea rax, [rdi + rsi*4 - 7]\n")
                text = routine.read_text(); assert text.count(before) == 1
                routine.write_text(text.replace(before, after, 1))
            elif label == "preserved-register":
                text = routine.read_text(); assert text.count("    ret\n") == 1
                routine.write_text(text.replace("    ret\n", "    mov rbx, 0\n    ret\n", 1))
            for name in ROLE_FILES:
                if name != "routine.S": assert (directory / name).read_bytes() == (root / pack / role / name).read_bytes()
            run(["cmake", "-S", ".", "-B", "build", "-DCMAKE_BUILD_TYPE=" + build_type, "-DCMAKE_C_COMPILER=" + cc, "-DCMAKE_ASM_COMPILER=" + cc], directory, "configure")
            run(["cmake", "--build", "build", "--verbose", "--parallel", "1"], directory, "build")
            success = label in ("completed", "reference", "release")
            ctest, _ = run(["ctest", "--test-dir", "build", "--output-on-failure"], directory, "ctest", expected=0 if success else None)
            assert ("100% tests passed" in ctest) == success
            stdout, stderr = run([str(directory / "build/contracts")], directory, "contracts", expected=0 if success else 1)
            assert ("10269 independent machine-model cases" in stdout) == success
            if label == "preserved-register": assert "preserved=0" in stderr
            (directory / "oracle-driver.c").write_text(ORACLE_DRIVER)
            run([cc, "-std=c17", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion", "-Werror", "-O2" if build_type == "Release" else "-O0", "-g", "oracle-driver.c", "abi_checks.S", "routine.S", "-o", "oracle"], directory, "oracle-build")
            observed, _ = run([str(directory / "oracle")], directory, "oracle", stdin=payload)
            rows = observed.splitlines(); assert len(rows) == len(inputs)
            failures = []
            for index, ((initial, incoming), row) in enumerate(zip(inputs, rows)):
                fields = row.split()
                assert len(fields) == (7 if mode == "memory" else 6) and fields[0] in ("0", "1")
                actual = [int(value, 16) for value in fields[1:]]
                expected = model(mode, initial, incoming)
                if fields[0] != "1" or actual != expected: failures.append(index)
            assert (not failures) == success
            demos = []
            if label != "preserved-register":
                for variant, extra in [("default", []), ("changed", ["--changed"])] if success else [("default", [])]:
                    output, _ = run([str(directory / "build/app"), *extra], directory, "app-" + variant, expected=0 if success else 78)
                    initial, incoming = demo_inputs(mode, bool(extra))
                    if success:
                        lines = output.splitlines()
                        assert lines[0] == f"initial={initial:016x} incoming={incoming:016x}"
                        assert [int(line.split("=")[1],16) for line in lines[1:]] == model(mode,initial,incoming)
                    else: assert output == ""
                    demos.append({"variant":variant,"stdout":output})
            raw = directory / "build/CMakeFiles/app.dir/routine.S.o"
            run(["objdump", "-d", "-M", "intel", str(raw)], directory, "routine-disassembly")
            run(["readelf", "-Ws", str(raw)], directory, "routine-symbols")
            proof["profiles"].append({"mode":mode,"label":label,"role":role,"buildType":build_type,"directory":str(directory.relative_to(args.proof.parent)),"success":success,"independentOracleRows":len(rows),"oracleMismatches":len(failures),"firstMismatch":failures[0] if failures else None,"routineObjectSha256":hashlib.sha256(raw.read_bytes()).hexdigest(),"appRuns":demos})
            if label in ("untouched", "completed"):
                initial, incoming = demo_inputs(mode, False)
                expected = model(mode, initial, incoming)
                if label == "untouched":
                    if mode == "memory": expected[4] &= 0xffffffff
                    else: expected[2] = (initial + incoming * 2 + 13) & MASK
                script = ["set pagination off", "set confirm off", "set startup-with-shell off", "set disable-randomization off", "set disassembly-flavor intel", "set language c"]
                script += ["break lab_stage" + str(i) for i in range(len(expected))]
                script.append("run")
                for index in range(len(expected)):
                    if index: script.append("continue")
                    if mode == "memory" and index == 0:
                        format_string = "STACK_BYTES=" + "%02x" * 16 + "\\n"
                        arguments = ", ".join(f"(unsigned int)*(unsigned char*)($rsp+{offset})" for offset in range(16))
                        script.append(f'printf "{format_string}", {arguments}')
                        script.append("x/16bx $rsp")
                    script += [f'printf "REG_BEFORE {index}=%016lx source=%016lx\\n", $rax, $rsi', "x/i $pc"]
                    if mode == "lea": script.append(f'printf "FLAGS_BEFORE {index}=%lx\\n", $eflags & 0x8c1')
                    script += ["si", f'printf "REG_AFTER {index}=%016lx\\n", $rax']
                    if mode == "lea": script.append(f'printf "FLAGS_AFTER {index}=%lx\\n", $eflags & 0x8c1')
                    script += ["si", f'printf "REG_MEMORY {index}=%016lx\\n", *(unsigned long long*)($rdx+{index*8})']
                script.append("continue")
                command = ["gdb", "-q", "-nx", "-batch"]
                for line in script: command.extend(["-ex", line])
                command.append(str(directory / "build/app"))
                trace, _ = run(command, directory, "gdb")
                for index, wanted in enumerate(expected):
                    before = 0 if index == 0 else expected[index-1]
                    assert f"REG_BEFORE {index}={before:016x} source={incoming:016x}" in trace
                    assert f"REG_AFTER {index}={wanted:016x}" in trace and f"REG_MEMORY {index}={wanted:016x}" in trace
                    if mode == "lea":
                        flags = compare_flags(initial, incoming)
                        assert f"FLAGS_BEFORE {index}={flags:x}" in trace and f"FLAGS_AFTER {index}={flags:x}" in trace
                if mode == "memory":
                    data = initial.to_bytes(8, "little") + incoming.to_bytes(8, "little")
                    assert "STACK_BYTES=" + data.hex() in trace
                assert len(re.findall(r"=> 0x[0-9a-f]+", trace)) >= len(expected)
                proof["debuggerTraces"].append({"mode":mode,"label":label,"path":str((directory / "gdb.stdout.txt").relative_to(args.proof.parent)),"actualStages":len(expected)})
        reference = work / (mode + "-reference")
        run([str(reference / "build/app"), "--unknown"], reference, "invalid-arguments", expected=64)
        proof["inputRefusals"].append({"mode":mode,"exitCode":64})
    proof.update(nativeExecuted=True, sourceUnchanged=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==sha for name,sha in sources.items()),
                 commandRecords=records, learnerCompletedOnly="routine.S", successfulProfiles=6, unfinishedProfiles=2, controlledOperationRegressions=2, preservedRegisterRegressions=2,
                 independentOracleRows=sum(row["independentOracleRows"] for row in proof["profiles"]), worksheetCompletionNotInferred=True)
    assert proof["sourceUnchanged"]
    args.proof.write_text(json.dumps(proof,indent=2)+"\n")
    print(json.dumps({key:proof[key] for key in ("compiler","nativeExecuted","successfulProfiles","independentOracleRows")}))


if __name__ == "__main__":
    main()
