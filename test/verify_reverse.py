"""Verify the unchanged mystery algorithm and a full-width C reconstruction."""
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
PACK = ROOT / "ASM6-Reverse-Engineering-Toy-Program"
parser = argparse.ArgumentParser()
parser.add_argument("--cc", choices=["clang", "gcc"], required=True)
parser.add_argument("--skip-debugger", action="store_true")
parser.add_argument("--proof", type=Path, required=True)
args = parser.parse_args()
assert platform.system() == "Linux" and platform.machine() == "x86_64"
args.proof.parent.mkdir(parents=True, exist_ok=True)
process_log = args.proof.with_suffix(".processes.jsonl")

def run(command, cwd, expected=0, input_data=None, timeout=120):
    command = [str(x) for x in command]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    child = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True)
    cleanup = "process exited"
    try:
        out, err = child.communicate(input=input_data, timeout=timeout)
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
        with process_log.open("a") as stream:
            stream.write(json.dumps(dict(parentTaskId=os.environ.get("CLASSES_FAMILY_TASK_ID", "assembly-reverse-native"),
                command=command, cwd=str(cwd), pid=child.pid, startTime=started,
                endTime=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                exitCode=child.returncode, timeoutSeconds=timeout,
                childProcessGroupCleanup=cleanup)) + "\n")
    assert (child.returncode != 0 if expected == "failure" else child.returncode == expected), (command, child.returncode, (out + err).decode(errors="replace"))
    return out, err

def hashes():
    return {str(f.relative_to(PACK)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in PACK.rglob("*") if f.is_file()}

def signed(number):
    bits = number % (1 << 64)
    return bits - (1 << 64) if bits >= (1 << 63) else bits

def oracle(value):
    stage = signed(abs(value))
    stage = signed(stage * 3 + 1) if stage % 2 else stage // 2
    return signed(stage + 7 if stage > 40 else stage - 5)

fixed = [0, 1, -1, 2, -2, 9, -9, 4, -4, 7, 18, 32, 41, -41, 13, -13,
         15, -15, 80, -80, 82, -82, (1 << 63) - 1, -(1 << 63), (1 << 63) - 2,
         -(1 << 63) + 1, 1 << 32, (1 << 32) + 1, -(1 << 32) - 1,
         (1 << 62) - 1, 1 << 62, (1 << 62) + 1, -(1 << 62) - 1]
inputs = list(fixed)
state = 0x5a17c9e42d0638bf
for _ in range(10000):
    state = (state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
    inputs.append(signed(state))
assert len(inputs) == 10033
oracle_input = "".join(f"{value} {oracle(value)}\n" for value in inputs).encode()
expected_contract = b"reverse cases passed: 10033\n"
default_values = [-9, -4, 7, 18, 32, 41]
def result_row(value):
    result = oracle(value)
    return f"input={value} mystery={result} reconstructed={result}\n".encode()
expected_demo = b"".join(result_row(value) for value in default_values)
invalid_cli = [[""], ["x"], ["+"], ["-"], [" 1"], ["1 "], ["0x10"],
               ["9223372036854775808"], ["-9223372036854775809"], ["1", "2"], ["-1x"]]
valid_cli = [-9, 13, 15, 80, 82, -(1 << 63), (1 << 63) - 1, (1 << 32) + 1]
before = hashes()
version = run([args.cc, "--version"], ROOT)[0].decode().splitlines()[0]
profiles, unfinished, regressions = [], [], []
with tempfile.TemporaryDirectory(prefix="assembly-reverse-") as work:
    temp = Path(work)
    for role in ["starter", "solution"]:
        shutil.copytree(PACK / role, temp / role)
    shutil.copytree(temp / "starter", temp / "completed")
    reconstruction = temp / "completed/reconstructed.c"
    code = reconstruction.read_text()
    old = """    /* TODO RECONSTRUCT_THRESHOLD: recover the signed comparison and both
       wrapping final offsets from the disassembly. Keep the earlier phases. */
    return signed_bits(bits);"""
    learner = """    const int64_t intermediate = signed_bits(bits);
    if (intermediate <= 40) bits -= UINT64_C(5);
    else bits += UINT64_C(7);
    return signed_bits(bits);"""
    assert code.count(old) == 1
    reconstruction.write_text(code.replace(old, learner))
    for f in (temp / "starter").iterdir():
        if f.name != "reconstructed.c":
            assert f.read_bytes() == (temp / "completed" / f.name).read_bytes()
    for role in ["starter", "solution", "completed"]:
        for profile in ["Debug", "Release"]:
            build = temp / (role + "-" + profile)
            run(["cmake", "-S", temp / role, "-B", build, "-DCMAKE_BUILD_TYPE=" + profile,
                 "-DCMAKE_C_COMPILER=" + args.cc, "-DCMAKE_ASM_COMPILER=" + args.cc,
                 "-DREVERSE_SANITIZE=ON"], temp)
            run(["cmake", "--build", build, "--parallel", "1"], temp)
            run(["ctest", "--test-dir", build, "--output-on-failure"], temp,
                expected="failure" if role == "starter" else 0)
            demo, err = run([build / "assembly_reverse"], temp, expected=78 if role == "starter" else 0)
            direct, _ = run([build / "reverse_contracts"], temp, expected=1 if role == "starter" else 0)
            independent, _ = run([build / "reverse_contracts", "--oracle"], temp,
                                 expected=1 if role == "starter" else 0, input_data=oracle_input)
            for argv in invalid_cli:
                output, error = run([build / "assembly_reverse", *argv], temp, expected=2)
                assert not output and b"signed decimal 64-bit" in error
            for value in valid_cli:
                output, error = run([build / "assembly_reverse", str(value)], temp,
                                    expected=78 if role == "starter" else 0)
                if role == "starter":
                    assert not output and b"unfinished or incorrect" in error
                else:
                    assert output == result_row(value) and not error
            if role == "starter":
                assert not demo and b"unfinished or incorrect" in err
                unfinished.append(dict(profile=profile, demoExit=78, contractExit=1, invalidCliRejected=11))
            else:
                assert demo == expected_demo and not err
                assert direct == independent == expected_contract
                profiles.append(dict(role=role, profile=profile, reverseCases=len(inputs),
                    independentPythonOracleCases=len(inputs), preservedRegistersPerFunction=6,
                    undefinedBehaviorSanitizer=True, invalidCliRejected=11,
                    validCliAccepted=8, demoOutput=demo.decode()))
    mutations = {
        "threshold-equality": ("reconstructed.c", "signed_bits(bits) > 40", "signed_bits(bits) >= 40"),
        "unsigned-threshold": ("reconstructed.c", "signed_bits(bits) > 40", "bits > UINT64_C(40)"),
        "wrong-offset": ("reconstructed.c", "? UINT64_C(7)", "? UINT64_C(8)"),
        "logical-shift": ("reconstructed.c", "(bits >> 1) | (bits & (UINT64_C(1) << 63))", "bits >> 1"),
        "mystery-branch": ("mystery.S", "\tjg .Lhigh_path", "\tjge .Lhigh_path"),
        "preserved-register": ("mystery.S", "mystery_score:\n", "mystery_score:\n\tmov rbx, 0\n")
    }
    for kind in [*mutations, "signed-overflow"]:
        folder = temp / kind
        shutil.copytree(temp / "solution", folder)
        if kind == "signed-overflow":
            (folder / "reconstructed.c").write_text('''#include "reverse.h"
int64_t student_reconstruction(int64_t value) {
    if (value < 0) value = -value;
    if (value & 1) value = value * 3 + 1;
    else value /= 2;
    return value > 40 ? value + 7 : value - 5;
}
''')
        else:
            name, old, new = mutations[kind]
            file = folder / name
            code = file.read_text()
            assert code.count(old) == 1, kind
            file.write_text(code.replace(old, new))
        run([args.cc, "-std=c17", "-O1", "-Wall", "-Wextra", "-Wpedantic",
             "-Wconversion", "-Werror", "-fsanitize=undefined", "-fno-sanitize-recover=undefined",
             "tests.c", "abi_checks.S", "mystery.S", "reconstructed.c", "-o", "broken"], folder)
        _, error = run([folder / "broken"], folder, expected="failure")
        if kind == "signed-overflow":
            assert b"runtime error" in error
        if kind == "preserved-register":
            assert b"callee-saved register contract failed" in error
        regressions.append(dict(kind=kind, rejected=True))
    disassembly = run(["objdump", "-d", "-M", "intel", temp / "solution-Debug/assembly_reverse"], temp)[0]
    assert b"<mystery_score>:" in disassembly and b"<student_reconstruction>:" in disassembly
    debugger = dict(status="not exercised in emulated local run")
    if not args.skip_debugger:
        trace, _ = run(["gdb", "--batch", "--nx", "-q", temp / "solution-Debug/assembly_reverse",
            "-ex", "set disassembly-flavor intel", "-ex", "tbreak *mystery_score", "-ex", "run",
            "-ex", 'printf "REVERSE-input=%lld\\n", $rdi', "-ex", "finish",
            "-ex", 'printf "REVERSE-result=%lld\\n", $rax', "-ex", "continue"], temp)
        assert b"REVERSE-input=-9" in trace and b"REVERSE-result=23" in trace
        assert b"input=41 mystery=131 reconstructed=131" in trace
        debugger = dict(status="accepted", trace=trace.decode())
assert not Path(work).exists() and before == hashes()
receipt = dict(event="verified-assembly-reverse", compiler=args.cc, compilerVersion=version,
    acceptedProfiles=profiles, unfinishedProfilesRejected=unfinished,
    controlledRegressions=regressions, independentLearnerCompletedOnly="reconstructed.c",
    independentOracle="Python arbitrary-precision arithmetic and floor division",
    debugger=debugger, sourceFilesUnchanged=True, temporaryBuildCleanup=True)
args.proof.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(dict(event=receipt["event"], compiler=args.cc, reverseCases=sum(p["reverseCases"] for p in profiles),
    acceptedProfiles=len(profiles), regressionsRejected=len(regressions), debugger=debugger["status"])))
