"""Observe pointer-table indirection and bounded overlapping byte copies."""
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

PACKS = {'table': 'ASM-15-unit-7-memory-addressing-and-data-structures-supplemental-2', 'overlap': 'ASM-16-unit-7-memory-addressing-and-data-structures-supplemental-3'}
ROLE_FILES = ("routine.S", "main.c", "lab.h", "model.c", "tests.c", "abi_checks.S", "CMakeLists.txt", "trace.md")
MASK = (1 << 64) - 1
FIXED = [0, 1, 2, 31, 32, 63, 64, 65, 127, 128, 255, 9223372036854775807, 9223372036854775808, 9223372036854775809, 12297829382473034410, 18446744073709551615]


def observed_model(mode, initial, incoming, label="reference"):
    if mode=="table":
        index=initial&3
        selected=((0 if label=="untouched" else index)+(incoming&3))&3
        tag=(incoming^(selected*0x1111))&0xffff
        if label=="wrong-operation": tag &= 0xff
        return [index,selected,((incoming>>16)^(selected*0x01010101))&0xffffffff,tag,selected*16]
    source,destination=initial&7,incoming&7
    count=min((initial>>3)&15,16-source,16-destination)
    data=list(range(1,17))
    backward=destination>source
    if label=="untouched": backward=not backward
    elif label=="wrong-operation": backward=False
    for offset in (range(count-1,-1,-1) if backward else range(count)):
        data[destination+offset]=data[source+offset]
    return [int.from_bytes(bytes(data[:8]),"little"),int.from_bytes(bytes(data[8:]),"little"),count,source,destination]

def model(mode,initial,incoming): return observed_model(mode,initial,incoming)
def unfinished_model(mode,initial,incoming): return observed_model(mode,initial,incoming,"untouched")
def demo_inputs(mode,changed):
    return (0,0) if changed else (0x010203040506070a,0x8123456789abcdef) if mode=="table" else (0x31,3)


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
    work = args.proof.parent / ("memory-layout-" + args.cc + "-observations")
    work.mkdir(exist_ok=False)
    records = []

    def run(argv, directory, label, expected=0, stdin=None, timeout=120):
        child = subprocess.Popen(argv, cwd=directory, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        record = {"parentTask": "assembly-memory-layout-native", "parentPid": os.getpid(), "pid": child.pid,
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
                before, after = ("    movzx r9d, WORD PTR [r8 + 8]\n", "    movzx r9d, BYTE PTR [r8 + 8]\n") if mode == "table" else ("    ja lab_backward\n", "    jmp lab_forward\n")
                text = routine.read_text(); assert text.count(before) == 1
                routine.write_text(text.replace(before, after, 1))
            elif label == "preserved-register":
                text = routine.read_text(); assert text.count("lab_return:\n    ret\n") == 1
                routine.write_text(text.replace("lab_return:\n    ret\n", "lab_return:\n    mov rbx, 0\n    ret\n", 1))
            for name in ROLE_FILES:
                if name != "routine.S": assert (directory / name).read_bytes() == (root / pack / role / name).read_bytes()
            run(["cmake", "-S", ".", "-B", "build", "-DCMAKE_BUILD_TYPE=" + build_type, "-DCMAKE_C_COMPILER=" + cc, "-DCMAKE_ASM_COMPILER=" + cc], directory, "configure")
            run(["cmake", "--build", "build", "--verbose", "--parallel", "1"], directory, "build")
            success = label in ("completed", "reference", "release")
            ctest, _ = run(["ctest", "--test-dir", "build", "--output-on-failure"], directory, "ctest", expected=0 if success else None)
            assert ("100% tests passed" in ctest) == success
            stdout, stderr = run([str(directory / "build/contracts")], directory, "contracts", expected=0 if success else 1)
            assert ("10269 independent memory-layout cases" in stdout) == success
            if label == "preserved-register": assert "preserved=0" in stderr
            (directory / "oracle-driver.c").write_text(ORACLE_DRIVER)
            run([cc, "-std=c17", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion", "-Werror", "-O2" if build_type == "Release" else "-O0", "-g", "oracle-driver.c", "abi_checks.S", "routine.S", "-o", "oracle"], directory, "oracle-build")
            observed, _ = run([str(directory / "oracle")], directory, "oracle", stdin=payload)
            rows = observed.splitlines(); assert len(rows) == len(inputs)
            failures = []
            for index, ((initial, incoming), row) in enumerate(zip(inputs, rows)):
                fields = row.split()
                assert len(fields) == 6 and fields[0] in ("0", "1")
                actual = [int(value, 16) for value in fields[1:]]
                expected = model(mode, initial, incoming)
                if fields[0] != "1" or actual != expected: failures.append(index)
            assert (not failures) == success
            demos = []
            if label != "preserved-register":
                for variant, extra in [("default", []), ("changed", ["--changed"])]:
                    demo_success = success or bool(extra)
                    output, _ = run([str(directory / "build/app"), *extra], directory, "app-" + variant, expected=0 if demo_success else 78)
                    initial, incoming = demo_inputs(mode, bool(extra))
                    if demo_success:
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
                expected = unfinished_model(mode, initial, incoming) if label == "untouched" else model(mode, initial, incoming)
                selected = ["lab_lookup","lab_selected"] if mode=="table" else ["lab_ready","lab_forward_load","lab_forward_store","lab_backward_load","lab_backward_store","lab_copy_done"]
                script = ["set pagination off","set confirm off","set startup-with-shell off","set disable-randomization off","set disassembly-flavor intel","set language c","break lab_operation","run","set $original_output = $rdx","set $entry_sp = $rsp","set $entry_return = *(unsigned long long*)$rsp","set $steps = 0"]
                for name in selected: script.append(f'printf "MEM_LABEL {name}=%016lx\\n", &{name}')
                script += ["while $pc != (unsigned long)&lab_return && $steps < 256",'printf "MEM_STEP pc=%016lx sp=%016lx a=%016lx count=%016lx src=%016lx dst=%016lx\\n", $pc,$rsp,$rax,$rcx,$r8,$r9']
                condition=" || ".join("$pc == (unsigned long)&"+name for name in selected)
                script += ["if "+condition]
                if mode=="table":
                    script += ['printf "MEM_TABLE base=%016lx p0=%016lx p1=%016lx p2=%016lx p3=%016lx selected=%016lx\\n", $rsp, *(unsigned long long*)($rsp+64),*(unsigned long long*)($rsp+72),*(unsigned long long*)($rsp+80),*(unsigned long long*)($rsp+88),$r8']
                else:
                    script += ['printf "MEM_BYTES base=%016lx lo=%016lx hi=%016lx\\n", $rsp,*(unsigned long long*)$rsp,*(unsigned long long*)($rsp+8)']
                script += ["end","x/i $pc","si","set $steps = $steps+1","end",'printf "MEM_RESTORED sp=%016lx original=%016lx return=%016lx expected=%016lx\\n",$rsp,$entry_sp,*(unsigned long long*)$rsp,$entry_return']
                for index in range(len(expected)): script.append(f'printf "FLOW_RESULT {index}=%016lx\\n",*(unsigned long long*)($original_output+{index*8})')
                script += ["si",'printf "MEM_RETURN pc=%016lx expected=%016lx sp=%016lx original=%016lx\\n",$pc,$entry_return,$rsp,$entry_sp',"continue"]
                commands=directory/"gdb.commands";commands.write_text("\n".join(script)+"\n")
                trace,_=run(["gdb","-q","-nx","-batch","-x",str(commands),str(directory/"build/app")],directory,"gdb")
                steps=len(re.findall(r"^MEM_STEP pc=",trace,re.M));assert 0<steps<256
                restored=re.search(r"MEM_RESTORED sp=([0-9a-f]+) original=([0-9a-f]+) return=([0-9a-f]+) expected=([0-9a-f]+)",trace)
                returned=re.search(r"MEM_RETURN pc=([0-9a-f]+) expected=([0-9a-f]+) sp=([0-9a-f]+) original=([0-9a-f]+)",trace)
                assert restored and returned and int(restored[1],16)==int(restored[2],16) and int(restored[3],16)==int(restored[4],16)
                assert int(returned[1],16)==int(returned[2],16)==int(restored[4],16) and int(returned[3],16)==int(returned[4],16)+8
                for index,wanted in enumerate(expected): assert f"FLOW_RESULT {index}={wanted:016x}" in trace
                if mode=="table":
                    rows=re.findall(r"MEM_TABLE base=([0-9a-f]+) p0=([0-9a-f]+) p1=([0-9a-f]+) p2=([0-9a-f]+) p3=([0-9a-f]+) selected=([0-9a-f]+)",trace)
                    assert len(rows)==2
                    for row in rows:
                        base=int(row[0],16)
                        assert [int(v,16) for v in row[1:5]]==[base+((i+(incoming&3))&3)*16 for i in range(4)]
                    assert int(rows[-1][-1],16)==int(rows[-1][0],16)+expected[-1]
                else:
                    assert "MEM_BYTES" in trace and trace.count("MEM_BYTES")>=14
                proof["debuggerTraces"].append({"mode":mode,"label":label,"path":str((directory / "gdb.stdout.txt").relative_to(args.proof.parent)),"actualSteps":steps,"expectedFinalFields":expected})
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
