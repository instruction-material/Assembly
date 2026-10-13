"""Verify the string's native contract and complete learner edits."""
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
PACK = ROOT / "ASM3-String-Length-and-Copy"
parser = argparse.ArgumentParser()
parser.add_argument("--cc", choices=["clang", "gcc"], required=True)
parser.add_argument("--skip-debugger", action="store_true")
parser.add_argument("--proof", type=Path, default=Path("output/string-proof.json"))
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
expected_default = b"strlen=9\nwide length=8 text=assembly\nsmall length=8 text=assem\nzero capacity length=8\n"
with tempfile.TemporaryDirectory(prefix="assembly-string-") as work:
    temp = Path(work)
    for role in ["starter", "solution"]:
        shutil.copytree(PACK / role, temp / role)
    shutil.copytree(temp / "starter", temp / "completed")
    path = temp / "completed/string_routines.S"
    code = path.read_text()
    marker = "\t/* TODO COPY_SOURCE_LENGTH: count the remaining source bytes to NUL.\n\t   Do not write more destination bytes; return the full source length. */\n\tmov rax, rcx\n\tret"
    completion = """    cmp BYTE PTR [rsi + rcx], 0
    je .Llearner_done
    inc rcx
    jmp .Lcount_tail
.Llearner_done:
    mov rax, rcx
    ret"""
    assert code.count(marker) == 1
    path.write_text(code.replace(marker, completion))
    for p in (temp / "starter").iterdir():
        if p.name != "string_routines.S":
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
            out, err = run([build / "assembly_strings"], temp, expected=78 if role == "starter" else 0)
            contracts, contract_err = run([build / "string_contracts"], temp,
                expected=1 if role == "starter" else 0)
            if role == "starter":
                assert not out and b"unfinished or incorrect" in err
                assert b"expected length=" in contract_err
                rejected.append(dict(profile=profile, demoExit=78, contractExit=1))
            else:
                assert out == expected_default and not err
                count = re.fullmatch(rb"(\d+) string cases accepted; bounded writes and unchanged source verified\n", contracts)
                assert count and int(count[1]) == 35900 and not contract_err
                profiles.append(dict(role=role, profile=profile, stringCases=35900,
                    preservedRegisters=6, guardPageAndReadonly=True,
                    zeroCapacityWithoutDestinationAccess=True, demoOutput=out.decode()))
    mutations = {
        "copied-length": ("\tjae .Lfinish_copy", "\tjae .Lwrong_length"),
        "missing-terminator": (".Lfinish_copy:\n\tmov BYTE PTR [rdi + rcx], 0", ".Lfinish_copy:\n\tnop"),
        "capacity-off-by-one": ("\tlea r8, [rdx - 1]", "\tmov r8, rdx"),
        "zero-capacity-write": ("asm_strlcpy_simple:\n", "asm_strlcpy_simple:\n    test rdx, rdx\n    jne .Lzero_write_skip\n    mov BYTE PTR [rdi], 0\n.Lzero_write_skip:\n"),
        "source-write": ("asm_strlcpy_simple:\n", "asm_strlcpy_simple:\n    mov BYTE PTR [rsi], 0\n"),
        "preserved-register": ("asm_strlcpy_simple:\n", "asm_strlcpy_simple:\n    mov rbx, 0\n"),
        "source-overread": (".Lstrlen_done:\n\tret", ".Lstrlen_done:\n    mov dl, BYTE PTR [rdi + rax + 1]\n\tret")
    }
    for name, (old, new) in mutations.items():
        folder = temp / name
        shutil.copytree(temp / "solution", folder)
        path = folder / "string_routines.S"
        code = path.read_text()
        assert code.count(old) == 1
        code = code.replace(old, new)
        if name == "copied-length":
            code = code.replace(".size asm_strlcpy_simple", ".Lwrong_length:\n    mov BYTE PTR [rdi + rcx], 0\n    mov rax, rcx\n    ret\n.size asm_strlcpy_simple")
        path.write_text(code)
        run([args.cc, "-std=c17", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion", "-Werror",
             "tests.c", "abi_checks.S", "string_routines.S", "-o", "broken"], folder)
        _, err = run([folder / "broken"], folder, expected="failure")
        if name == "preserved-register":
            assert b"callee-saved register contract failed" in err
        regressions.append(dict(kind=name, rejected=True))
    disassembly, _ = run(["objdump", "-d", "-M", "intel", temp / "solution-Debug/assembly_strings"], temp)
    assert b"<asm_strlen_simple>:" in disassembly and b"<asm_strlcpy_simple>:" in disassembly
    debugger = dict(status="not exercised in emulated local run")
    if not args.skip_debugger:
        trace, _ = run(["gdb", "--batch", "--nx", "-q", temp / "solution-Debug/assembly_strings",
            "-ex", "set disassembly-flavor intel",
            "-ex", "tbreak asm_strlcpy_simple if $rdx == 6", "-ex", "run",
            "-ex", 'printf "STRING-capacity=%lu\\n", $rdx',
            "-ex", "set $saved_dest = (char *)$rdi", "-ex", "finish",
            "-ex", 'printf "STRING-source-length=%lu\\n", $rax',
            "-ex", "x/s $saved_dest", "-ex", "continue"], temp)
        assert b"STRING-capacity=6" in trace and b"STRING-source-length=8" in trace and b'"assem"' in trace
        assert b"small length=8 text=assem" in trace and b"zero capacity length=8" in trace
        debugger = dict(status="accepted", trace=trace.decode())
assert not Path(work).exists() and before == hashes()
receipt = dict(event="verified-assembly-string", compiler=args.cc, compilerVersion=version,
    acceptedProfiles=profiles, unfinishedProfilesRejected=rejected, controlledRegressions=regressions,
    independentLearnerCompletedOnly="string_routines.S", debugger=debugger,
    sourceFilesUnchanged=True, temporaryBuildCleanup=True)
args.proof.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(dict(event=receipt["event"], compiler=args.cc, stringCases=sum(p["stringCases"] for p in profiles),
    acceptedProfiles=len(profiles), regressionsRejected=len(regressions), debugger=debugger["status"])))
