"""Verify the array's native contract and complete learner edits."""
import argparse
import re
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "ASM2-Array-Sum-and-Search"
parser = argparse.ArgumentParser()
parser.add_argument("--cc", choices=["clang", "gcc"], required=True)
parser.add_argument("--skip-debugger", action="store_true")
parser.add_argument("--proof", type=Path, default=Path("output/array-proof.json"))
args = parser.parse_args()
assert platform.system() == "Linux" and platform.machine() == "x86_64"
args.proof.parent.mkdir(parents=True, exist_ok=True)
log = args.proof.with_suffix(".processes.jsonl")

def run(argv, cwd, expected=0, timeout=120):
    argv = [str(x) for x in argv]
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    child = subprocess.Popen(
        argv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    cleanup = "process exited"
    try:
        out, err = child.communicate(timeout=timeout)
    except BaseException:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.communicate()
        cleanup = "child process group terminated"
        raise
    finally:
        with log.open("a") as stream:
            stream.write(
                json.dumps(
                    dict(
                        parentTaskId=os.environ.get(
                            "CLASSES_FAMILY_TASK_ID", "assembly-opening-native"
                        ),
                        cwd=str(cwd),
                        command=argv,
                        pid=child.pid,
                        startTime=start,
                        endTime=datetime.datetime.now(
                            datetime.timezone.utc
                        ).isoformat(),
                        exitCode=child.returncode,
                        timeoutSeconds=timeout,
                        childProcessGroupCleanup=cleanup,
                    )
                )
                + "\n"
            )
    assert (
        child.returncode != 0 if expected == "failure" else child.returncode == expected
    ), (argv, child.returncode, (out + err).decode(errors="replace"))
    return out, err


def hashes():
    return {str(p.relative_to(PACK)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in PACK.rglob("*") if p.is_file()}


before = hashes()
version = run([args.cc, "--version"], ROOT)[0].decode().splitlines()[0]
profiles, rejected, regressions = [], [], []
expected_default = b"sum=48\nfirst >= 10=0\nfirst >= 18=3\nfirst >= 20=-1\n"
with tempfile.TemporaryDirectory(prefix="assembly-array-") as work:
    temp = Path(work)
    for role in ["starter", "solution"]:
        shutil.copytree(PACK / role, temp / role)
    shutil.copytree(temp / "starter", temp / "completed")
    path = temp / "completed/array_routines.S"
    code = path.read_text()
    start = code.index("asm_find_first_ge:\n")
    end = code.index(".size asm_find_first_ge")
    code = code[:start] + """asm_find_first_ge:
    mov rax, -1
    test rsi, rsi
    jle .Lcompleted_done
    xor ecx, ecx
.Lcompleted_next:
    cmp edx, DWORD PTR [rdi + rcx * 4]
    jle .Lcompleted_found
    inc rcx
    cmp rcx, rsi
    jl .Lcompleted_next
    ret
.Lcompleted_found:
    mov rax, rcx
.Lcompleted_done:
    ret
""" + code[end:]
    path.write_text(code)
    for p in (temp / "starter").iterdir():
        if p.name != "array_routines.S":
            assert p.read_bytes() == (temp / "completed" / p.name).read_bytes()
    for role in ["starter", "solution", "completed"]:
        for profile in ["Debug", "Release"]:
            build = temp / (role + "-" + profile)
            run(["cmake", "-S", temp / role, "-B", build,
                 "-DCMAKE_BUILD_TYPE=" + profile, "-DCMAKE_C_COMPILER=" + args.cc,
                 "-DCMAKE_ASM_COMPILER=" + args.cc], temp)
            run(["cmake", "--build", build, "--parallel", "1"], temp)
            run(["ctest", "--test-dir", build, "--output-on-failure"], temp,
                expected="failure" if role == "starter" else 0)
            out, err = run([build / "assembly_array"], temp, expected=78 if role == "starter" else 0)
            contracts, contract_err = run([build / "array_contracts"], temp,
                expected=1 if role == "starter" else 0)
            if role == "starter":
                assert not out and b"unfinished or incorrect" in err
                assert b"expected=" in contract_err
                rejected.append(dict(profile=profile, demoExit=78, contractExit=1))
            else:
                assert out == expected_default and not err
                count = re.fullmatch(rb"(\d+) array cases accepted; bounded reads and unchanged input verified\n", contracts)
                assert count and int(count[1]) == 11280 and not contract_err
                profiles.append(dict(role=role, profile=profile, arrayCases=11280,
                    preservedRegisters=6, guardPageAndReadonly=True,
                    emptyAndNegativeCountWithoutDereference=True, demoOutput=out.decode()))
    mutations = {
        "sign-extension": ("    movsxd r8, DWORD PTR [rdi + rcx * 4]", "    mov r8d, DWORD PTR [rdi + rcx * 4]"),
        "unsigned-search": ("    jge .Lfound", "    jae .Lfound"),
        "wrong-index": ("    mov rax, rcx", "    lea rax, [rcx + 1]"),
        "overread": ("    jge .Lsum_done", "    jg .Lsum_done"),
        "input-write": ("asm_sum_array:\n", "asm_sum_array:\n    test rsi, rsi\n    jle .Lwrite_skip\n    mov DWORD PTR [rdi], 0\n.Lwrite_skip:\n"),
        "preserved-register": ("asm_sum_array:\n", "asm_sum_array:\n    mov rbx, 0\n")
    }
    for name, (old, new) in mutations.items():
        folder = temp / name
        shutil.copytree(temp / "solution", folder)
        path = folder / "array_routines.S"
        code = path.read_text()
        assert code.count(old) == 1
        path.write_text(code.replace(old, new))
        run([args.cc, "-std=c17", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion", "-Werror",
             "tests.c", "abi_checks.S", "array_routines.S", "-o", "broken"], folder)
        _, err = run([folder / "broken"], folder, expected="failure")
        if name == "preserved-register":
            assert b"callee-saved register contract failed" in err
        regressions.append(dict(kind=name, rejected=True))
    disassembly, _ = run(["objdump", "-d", "-M", "intel", temp / "solution-Debug/assembly_array"], temp)
    assert b"<asm_sum_array>:" in disassembly and b"<asm_find_first_ge>:" in disassembly and b"movsxd" in disassembly
    debugger = dict(status="not exercised in emulated local run")
    if not args.skip_debugger:
        trace, _ = run(["gdb", "--batch", "--nx", "-q", temp / "solution-Debug/assembly_array",
            "-ex", "set disassembly-flavor intel", "-ex", "tbreak asm_find_first_ge", "-ex", "run",
            "-ex", 'printf "ARRAY-input=%ld,%d\\n", $rsi, $edx',
            "-ex", "x/7wd $rdi", "-ex", "finish",
            "-ex", 'printf "ARRAY-output=%ld\\n", $rax', "-ex", "continue"], temp)
        assert b"ARRAY-input=7,10" in trace and b"ARRAY-output=0" in trace and b"first >= 18=3" in trace
        debugger = dict(status="accepted", trace=trace.decode())
assert not Path(work).exists() and before == hashes()
receipt = dict(event="verified-assembly-array", compiler=args.cc, compilerVersion=version,
    acceptedProfiles=profiles, unfinishedProfilesRejected=rejected, controlledRegressions=regressions,
    independentLearnerCompletedOnly="array_routines.S", debugger=debugger,
    sourceFilesUnchanged=True, temporaryBuildCleanup=True)
args.proof.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(dict(event=receipt["event"], compiler=args.cc, arrayCases=sum(p["arrayCases"] for p in profiles),
    acceptedProfiles=len(profiles), regressionsRejected=len(regressions), debugger=debugger["status"])))
