"""Verify the helper's native contract and complete learner edits."""
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
PACK = ROOT / "ASM4-Call-C-Helper-from-Assembly"
parser = argparse.ArgumentParser()
parser.add_argument("--cc", choices=["clang", "gcc"], required=True)
parser.add_argument("--skip-debugger", action="store_true")
parser.add_argument("--proof", type=Path, default=Path("output/helper-proof.json"))
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
expected_default = b"scaled and clamped=40\nscaled and clamped=25\n"
with tempfile.TemporaryDirectory(prefix="assembly-helper-") as work:
    temp = Path(work)
    for role in ["starter", "solution"]:
        shutil.copytree(PACK / role, temp / role)
    shutil.copytree(temp / "starter", temp / "completed")
    path = temp / "completed/scale_and_clamp.S"
    code = path.read_text()
    marker = "\t/* TODO CALL_CLAMP: align the stack, map the three C arguments,\n\t   call clamp_to_range, and restore the stack before returning. */\n\tret"
    completion = """    push r12
    mov rdi, rax
    mov rsi, rcx
    mov rdx, r8
    call clamp_to_range
    pop r12
    ret"""
    assert code.count(marker) == 1
    path.write_text(code.replace(marker, completion))
    for p in (temp / "starter").iterdir():
        if p.name != "scale_and_clamp.S":
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
            out, err = run([build / "assembly_helper"], temp, expected=78 if role == "starter" else 0)
            contracts, contract_err = run([build / "helper_contracts"], temp,
                expected=1 if role == "starter" else 0)
            if role == "starter":
                assert not out and b"unfinished or incorrect" in err
                assert b"helper invocation or argument contract failed" in contract_err
                rejected.append(dict(profile=profile, demoExit=78, contractExit=1))
            else:
                assert out == expected_default and not err
                count = re.fullmatch(rb"(\d+) helper cases accepted; call arguments and stack alignment verified\n", contracts)
                assert count and int(count[1]) == 11280 and not contract_err
                profiles.append(dict(role=role, profile=profile, helperCases=11280,
                    preservedRegisters=6, helperInvocationsPerCase=2,
                    exactHelperArguments=True, helperEntryStackMod16=8,
                    guardedReadonlyInput=True, demoOutput=out.decode()))
    mutations = {
        "sign-extension": ("scale_and_clamp.S", "\tmovsxd r10, DWORD PTR [rdi + r9 * 4]", "\tmov r10d, DWORD PTR [rdi + r9 * 4]"),
        "wrong-arguments": ("scale_and_clamp.S", "\tmov rsi, rcx\n\tmov rdx, r8", "\tmov rsi, r8\n\tmov rdx, rcx"),
        "missing-helper-call": ("scale_and_clamp.S", "\tcall clamp_to_range", "\tnop"),
        "misaligned-stack": ("scale_and_clamp.S", "\tpush rbp\n\tmov rbp, rsp", ""),
        "preserved-register": ("scale_and_clamp.S", "asm_scaled_clamped_sum:\n", "asm_scaled_clamped_sum:\n    mov rbx, 0\n"),
        "product-width": ("scale_and_clamp.S", "\timul rax, rdx", "\timul eax, edx"),
        "wrong-clamp": ("helper.c", "if (value < min_value) return min_value;", "if (value < min_value) return max_value;")
    }
    for name, (filename, old, new) in mutations.items():
        folder = temp / name
        shutil.copytree(temp / "solution", folder)
        path = folder / filename
        code = path.read_text()
        assert code.count(old) == 1
        code = code.replace(old, new)
        if name == "misaligned-stack":
            assert code.count("\tpop rbp") == 1
            code = code.replace("\tpop rbp", "")
        path.write_text(code)
        run([args.cc, "-DASSEMBLY_HELPER_PROBE", "-std=c17", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion", "-Werror",
             "tests.c", "abi_checks.S", "scale_and_clamp.S", "helper.c", "-o", "broken"], folder)
        _, err = run([folder / "broken"], folder, expected="failure")
        if name == "preserved-register":
            assert b"callee-saved register contract failed" in err
        if name == "misaligned-stack":
            assert b"helper entry stack alignment contract failed" in err
        regressions.append(dict(kind=name, rejected=True))
    disassembly, _ = run(["objdump", "-d", "-M", "intel", temp / "solution-Debug/assembly_helper"], temp)
    assert b"<asm_scaled_clamped_sum>:" in disassembly and b"<clamp_to_range>:" in disassembly
    debugger = dict(status="not exercised in emulated local run")
    if not args.skip_debugger:
        trace, _ = run(["gdb", "--batch", "--nx", "-q", temp / "solution-Debug/assembly_helper",
            "-ex", "set disassembly-flavor intel", "-ex", "tbreak *clamp_to_range", "-ex", "run",
            "-ex", 'printf "HELPER-input=%ld,%ld,%ld\\n", $rdi, $rsi, $rdx',
            "-ex", 'printf "HELPER-stack-mod16=%lu\\n", ((unsigned long)$rsp & 15)',
            "-ex", "finish", "-ex", 'printf "HELPER-output=%ld\\n", $rax', "-ex", "continue"], temp)
        assert b"HELPER-input=48,-20,40" in trace and b"HELPER-stack-mod16=8" in trace
        assert b"HELPER-output=40" in trace and b"scaled and clamped=25" in trace
        debugger = dict(status="accepted", trace=trace.decode())
assert not Path(work).exists() and before == hashes()
receipt = dict(event="verified-assembly-helper", compiler=args.cc, compilerVersion=version,
    acceptedProfiles=profiles, unfinishedProfilesRejected=rejected, controlledRegressions=regressions,
    independentLearnerCompletedOnly="scale_and_clamp.S", debugger=debugger,
    sourceFilesUnchanged=True, temporaryBuildCleanup=True)
args.proof.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(dict(event=receipt["event"], compiler=args.cc, helperCases=sum(p["helperCases"] for p in profiles),
    acceptedProfiles=len(profiles), regressionsRejected=len(regressions), debugger=debugger["status"])))
