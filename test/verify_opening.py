"""Verify the opening project on its required Linux x86-64 target."""

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
PACK = ROOT / "ASM-04-asm0-setup-and-tooling"
parser = argparse.ArgumentParser()
parser.add_argument("--cc", choices=["clang", "gcc"], required=True)
parser.add_argument(
    "--skip-debugger",
    action="store_true",
    help="For emulated local runs only; CI must exercise the debugger.",
)
parser.add_argument("--proof", type=Path, default=Path("output/opening-proof.json"))
args = parser.parse_args()
assert platform.system() == "Linux" and platform.machine() == "x86_64", (
    "Use the specified Linux x86-64 lab"
)
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
    return {
        str(f.relative_to(PACK)): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in PACK.rglob("*")
        if f.is_file()
    }


before = hashes()
profiles = []
rejected = []
regressions = []
versions = run([args.cc, "--version"], ROOT)[0].decode().splitlines()[0]
with tempfile.TemporaryDirectory(prefix="assembly-opening-") as work:
    temp = Path(work)
    for role in ["starter", "solution"]:
        shutil.copytree(PACK / role, temp / role)
    shutil.copytree(temp / "starter", temp / "completed")
    code = temp / "completed/routine.S"
    original = code.read_text()
    marker = "    /* TODO ASM_TRANSFORM: return the low 32 bits of 2 * input + 5. */\n    mov eax, edi"
    assert original.count(marker) == 1
    code.write_text(
        original.replace(marker, "    lea eax, [rdi + rdi]\n    add eax, 5")
    )
    for f in (temp / "starter").iterdir():
        if f.name != "routine.S":
            assert f.read_bytes() == (temp / "completed" / f.name).read_bytes()
    for role in ["starter", "solution", "completed"]:
        source = temp / role
        for profile in ["Debug", "Release"]:
            build = temp / (role + "-" + profile)
            run(
                [
                    "cmake",
                    "-S",
                    source,
                    "-B",
                    build,
                    "-DCMAKE_BUILD_TYPE=" + profile,
                    "-DCMAKE_C_COMPILER=" + args.cc,
                    "-DCMAKE_ASM_COMPILER=" + args.cc,
                ],
                temp,
            )
            run(["cmake", "--build", build, "--parallel", "1"], temp)
            run(
                ["ctest", "--test-dir", build, "--output-on-failure"],
                temp,
                expected="failure" if role == "starter" else 0,
            )
            out, err = run(
                [build / "assembly_demo"], temp, expected=78 if role == "starter" else 0
            )
            contracts, contract_err = run(
                [build / "assembly_contracts"],
                temp,
                expected=1 if role == "starter" else 0,
            )
            if role == "starter":
                assert not out and b"unfinished or incorrect" in err
                assert b"input=0: expected=5 actual=0" in contract_err
                rejected.append(
                    dict(role=role, profile=profile, demoExit=78, contractExit=1)
                )
            else:
                assert out == b"total=100\n" and not err
                assert (
                    contracts == b"10012 transform cases accepted\n"
                    and not contract_err
                )
                profiles.append(
                    dict(
                        role=role,
                        profile=profile,
                        arithmeticCases=10012,
                        preservedRegisters=6,
                        demoOutput=out.decode(),
                    )
                )
    for name in ["offset", "preserved-register"]:
        folder = temp / name
        shutil.copytree(temp / "solution", folder)
        path = folder / "routine.S"
        text = path.read_text()
        if name == "offset":
            assert text.count("[rdi + rdi + 5]") == 1
            text = text.replace("[rdi + rdi + 5]", "[rdi + rdi + 6]")
        else:
            text = text.replace("    lea eax,", "    mov rbx, 0\n    lea eax,")
        path.write_text(text)
        run(
            [
                args.cc,
                "-std=c17",
                "-Wall",
                "-Wextra",
                "-Wpedantic",
                "-Wconversion",
                "-Werror",
                "tests.c",
                "abi_checks.S",
                "routine.S",
                "-o",
                "broken",
            ],
            folder,
        )
        _, err = run([folder / "broken"], folder, expected=1)
        assert (
            b"expected=5 actual=6" in err
            if name == "offset"
            else b"callee-saved register contract failed" in err
        )
        regressions.append(dict(kind=name, rejected=True))
    disassembly, _ = run(
        ["objdump", "-d", "-M", "intel", temp / "solution-Debug/assembly_demo"], temp
    )
    assert b"<transform_value>:" in disassembly and b"lea" in disassembly
    debugger = dict(status="not exercised in emulated local run")
    if not args.skip_debugger:
        trace, _ = run(
            [
                "gdb",
                "--batch",
                "--nx",
                "-q",
                temp / "solution-Debug/assembly_demo",
                "-ex",
                "set disassembly-flavor intel",
                "-ex",
                "tbreak transform_value",
                "-ex",
                "run",
                "-ex",
                'printf "ABI-input=%d\\n", $edi',
                "-ex",
                "stepi",
                "-ex",
                'printf "ABI-output=%d\\n", $eax',
                "-ex",
                "continue",
            ],
            temp,
        )
        assert (
            b"ABI-input=0" in trace
            and b"ABI-output=5" in trace
            and b"total=100" in trace
        )
        debugger = dict(status="accepted", trace=trace.decode())
assert not Path(work).exists() and before == hashes()
receipt = dict(
    event="verified-assembly-opening",
    compiler=args.cc,
    compilerVersion=versions,
    target="Linux x86-64 System V",
    acceptedProfiles=profiles,
    unfinishedProfilesRejected=rejected,
    controlledRegressions=regressions,
    independentLearnerCompletedOnly="routine.S",
    debugger=debugger,
    sourceFilesUnchanged=True,
    temporaryBuildCleanup=True,
)
args.proof.write_text(json.dumps(receipt, indent=2) + "\n")
print(
    json.dumps(
        dict(
            event=receipt["event"],
            compiler=args.cc,
            acceptedProfiles=len(profiles),
            arithmeticCases=sum(x["arithmeticCases"] for x in profiles),
            unfinishedProfilesRejected=len(rejected),
            controlledRegressionsRejected=len(regressions),
            debugger=debugger["status"],
            sourceFilesUnchanged=True,
            temporaryBuildCleanup=True,
        )
    )
)
