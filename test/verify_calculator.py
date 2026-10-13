"""Verify the calculator's native contract and complete learner edits."""
import argparse
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
PACK = ROOT / "ASM1-Integer-Calculator"
parser = argparse.ArgumentParser()
parser.add_argument("--cc", choices=["clang", "gcc"], required=True)
parser.add_argument("--skip-debugger", action="store_true")
parser.add_argument("--proof", type=Path, default=Path("output/calculator-proof.json"))
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
expected_default = b"12 + 5 => 17\n12 - 5 => 7\n7 * 6 => 42\n21 / 3 => 7\n42 & 15 => 10\n42 ^ 15 => 37\n"
with tempfile.TemporaryDirectory(prefix="assembly-calculator-") as work:
    temp = Path(work)
    for role in ["starter", "solution"]:
        shutil.copytree(PACK / role, temp / role)
    shutil.copytree(temp / "starter", temp / "completed")
    path = temp / "completed/calculator.S"
    code = path.read_text()
    changes = {
        "    /* TODO CALC_DIV: form RDX:RAX and divide a valid signed pair. */\n    xor eax, eax": "    mov rax, rdi\n    cqo\n    idiv rsi",
        "    /* TODO CALC_AND: return the 64-bit bitwise intersection. */\n    xor eax, eax": "    mov rax, rsi\n    and rax, rdi",
        "    /* TODO CALC_XOR: return the 64-bit bitwise difference. */\n    xor eax, eax": "    mov rax, rsi\n    xor rax, rdi"
    }
    for marker, replacement in changes.items():
        assert code.count(marker) == 1
        code = code.replace(marker, replacement)
    path.write_text(code)
    for p in (temp / "starter").iterdir():
        if p.name != "calculator.S":
            assert p.read_bytes() == (temp / "completed" / p.name).read_bytes()
    invalid_cli = [["/", "3", "0"], ["/", "-9223372036854775808", "-1"],
        ["?", "1", "2"], ["+", "9223372036854775808", "0"],
        ["+", "-9223372036854775809", "0"], ["+", "1x", "2"],
        ["+", "", "2"], ["+", "1"], ["+", " 1", "2"]]
    valid_cli = [("+", "12", "5", "17"), ("-", "12", "5", "7"),
        ("*", "7", "6", "42"), ("/", "-21", "3", "-7"),
        ("/", "21", "-3", "-7"), ("/", "-21", "-3", "7"),
        ("&", "42", "15", "10"), ("^", "42", "15", "37"),
        ("+", "4294967308", "5", "4294967313"),
        ("+", "9223372036854775807", "1", "-9223372036854775808"),
        ("*", "9223372036854775807", "2", "-2"),
        ("/", "-9223372036854775808", "1", "-9223372036854775808")]
    for role in ["starter", "solution", "completed"]:
        for profile in ["Debug", "Release"]:
            build = temp / (role + "-" + profile)
            run(["cmake", "-S", str(temp / role), "-B", str(build),
                "-DCMAKE_BUILD_TYPE=" + profile, "-DCMAKE_C_COMPILER=" + args.cc,
                "-DCMAKE_ASM_COMPILER=" + args.cc], temp)
            run(["cmake", "--build", str(build), "--parallel", "1"], temp)
            run(["ctest", "--test-dir", str(build), "--output-on-failure"], temp,
                expected="failure" if role == "starter" else 0)
            exe = str(build / "assembly_calculator")
            out, err = run([exe], temp, expected=78 if role == "starter" else 0)
            contracts, contract_err = run([str(build / "calculator_contracts")], temp,
                expected=1 if role == "starter" else 0)
            for argv in invalid_cli:
                invalid_out, invalid_err = run([exe, *argv], temp, expected=2)
                assert not invalid_out and b"signed decimal 64-bit" in invalid_err
            if role == "starter":
                assert not out and b"unfinished or incorrect" in err
                assert b"expected=" in contract_err
                rejected.append(dict(profile=profile, demoExit=78, invalidInputsRejected=len(invalid_cli)))
            else:
                assert out == expected_default and not err
                assert contracts == b"12589 calculator cases accepted; invalid divisions guarded\n" and not contract_err
                for op, left, right, expected in valid_cli:
                    cli_out, cli_err = run([exe, op, left, right], temp)
                    assert cli_out == ("result=" + expected + "\n").encode() and not cli_err
                profiles.append(dict(role=role, profile=profile, arithmeticCases=12589,
                    invalidDivisionGuards=2, preservedRegisters=6, invalidInputsRejected=len(invalid_cli),
                    validCliCases=len(valid_cli), demoOutput=out.decode()))
    mutations = {"width": ("    mov rax, rdi\n    add rax, rsi", "    mov eax, edi\n    add rax, rsi"),
        "bitwise": ("    and rax, rsi", "    or rax, rsi"),
        "dividend": ("    cqo", "    xor edx, edx"),
        "preserved-register": ("asm_eval_expression:\n", "asm_eval_expression:\n    mov rbx, 0\n")}
    for name, (old, new) in mutations.items():
        folder = temp / name
        shutil.copytree(temp / "solution", folder)
        path = folder / "calculator.S"
        code = path.read_text()
        assert code.count(old) == 1
        path.write_text(code.replace(old, new))
        run([args.cc, "-std=c17", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion", "-Werror",
            "tests.c", "abi_checks.S", "calculator.S", "-o", "broken"], folder)
        _, err = run([str(folder / "broken")], folder, expected="failure")
        if name == "preserved-register":
            assert b"callee-saved register contract failed" in err
        regressions.append(dict(kind=name, rejected=True))
    disassembly, _ = run(["objdump", "-d", "-M", "intel", str(temp / "solution-Debug/assembly_calculator")], temp)
    assert b"<asm_eval_expression>:" in disassembly and b"idiv" in disassembly
    debugger = dict(status="not exercised in emulated local run")
    if not args.skip_debugger:
        trace, _ = run(["gdb", "--batch", "--nx", "-q", str(temp / "solution-Debug/assembly_calculator"),
            "-ex", "set disassembly-flavor intel", "-ex", "tbreak asm_eval_expression", "-ex", "run",
            "-ex", 'printf "CALC-input=%ld,%ld,%u\\n", $rdi, $rsi, $dl',
            "-ex", "finish", "-ex", 'printf "CALC-output=%ld\\n", $rax', "-ex", "continue"], temp)
        assert b"CALC-input=12,5,43" in trace and b"CALC-output=17" in trace and b"42 ^ 15 => 37" in trace
        debugger = dict(status="accepted", trace=trace.decode())
assert not Path(work).exists() and before == hashes()
receipt = dict(event="verified-assembly-calculator", compiler=args.cc, compilerVersion=version,
    acceptedProfiles=profiles, unfinishedProfilesRejected=rejected, controlledRegressions=regressions,
    independentLearnerCompletedOnly="calculator.S", debugger=debugger,
    sourceFilesUnchanged=True, temporaryBuildCleanup=True)
args.proof.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(dict(event=receipt["event"], compiler=args.cc, arithmeticCases=sum(p["arithmeticCases"] for p in profiles),
    acceptedProfiles=len(profiles), regressionsRejected=len(regressions), debugger=debugger["status"])))
