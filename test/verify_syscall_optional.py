"""Exercise actual owned-descriptor kernel calls and retain native evidence."""
import argparse
import ast
import errno
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

PACKS = {
    "write": "ASM-17-unit-8-system-calls-and-runtime-interaction-supplemental-2",
    "openat": "ASM-18-unit-8-system-calls-and-runtime-interaction-supplemental-3",
}
ROLE_FILES = ("routine.S", "main.c", "lab.h", "tests.c", "abi_checks.S", "CMakeLists.txt", "trace.md")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", choices=("clang", "gcc"), required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    ast.parse(Path(__file__).read_text(), feature_version=(3, 10))
    sources = {}
    for mode, pack in PACKS.items():
        changed = [name for name in ROLE_FILES if (root / pack / "starter" / name).read_bytes() != (root / pack / "solution" / name).read_bytes()]
        assert changed == ["routine.S"]
        for name in ["README.md"] + [role + "/" + name for role in ("starter", "solution") for name in ROLE_FILES]:
            sources[pack + "/" + name] = hashlib.sha256((root / pack / name).read_bytes()).hexdigest()
    assert len(sources) == 30
    args.proof = args.proof.resolve()
    args.proof.parent.mkdir(parents=True, exist_ok=True)
    proof = {"sourceFiles": sources, "compiler": args.cc, "nativeExecuted": False, "profiles": [], "debuggerTraces": [], "inputRefusals": []}
    if args.source_only:
        args.proof.write_text(json.dumps(proof, indent=2) + "\n")
        print("Source parity and Python 3.10 syntax checked; native verification not executed")
        return
    assert sys.platform == "linux" and platform.machine().lower() in ("x86_64", "amd64")
    assert os.geteuid() != 0, "Run these owned lab processes as an ordinary user"
    cc = shutil.which(args.cc)
    assert cc and all(shutil.which(name) for name in ("cmake", "ctest", "strace", "gdb", "objdump", "readelf"))
    work = args.proof.parent / ("syscall-" + args.cc + "-observations")
    work.mkdir(exist_ok=False)
    records = []

    def run(argv, cwd, label, expected=0, timeout=120):
        child = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        record = {"parentTask": "assembly-syscall-optional-native", "parentPid": os.getpid(), "pid": child.pid,
                  "cwd": str(cwd), "command": argv, "startTime": time.time(), "timeoutSeconds": timeout}
        logs = args.proof.with_suffix(".processes.jsonl")
        with logs.open("a") as stream:
            stream.write(json.dumps(dict(record, event="start")) + "\n")
        cleanup = "process exited"
        try:
            stdout, stderr = child.communicate(timeout=timeout)
        except BaseException:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                stdout, stderr = child.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                stdout, stderr = child.communicate()
            cleanup = "owned process group terminated and reaped"
            raise
        finally:
            record.update(endTime=time.time(), exitCode=child.returncode, childProcessGroupCleanup=cleanup)
            with logs.open("a") as stream:
                stream.write(json.dumps(dict(record, event="end")) + "\n")
        prefix = cwd / label
        prefix.with_suffix(".stdout.txt").write_bytes(stdout)
        prefix.with_suffix(".stderr.txt").write_bytes(stderr)
        records.append(record)
        assert child.returncode == expected if expected is not None else child.returncode != 0, (label, child.returncode, stderr.decode(errors="replace"))
        return stdout.decode(), stderr.decode()

    version, _ = run([cc, "--version"], work, "compiler-version")
    proof["compilerVersion"] = version
    for mode, pack in PACKS.items():
        symbol = "lab_" + mode
        for label, role, build_type in [("untouched", "starter", "Debug"), ("completed", "starter", "Debug"),
                                        ("reference", "solution", "Debug"), ("release", "solution", "Release"),
                                        ("wrong-call-or-argument", "solution", "Debug"), ("preserved-register", "solution", "Release")]:
            directory = work / (mode + "-" + label)
            shutil.copytree(root / pack / role, directory)
            routine = directory / "routine.S"
            if label == "completed":
                routine.write_bytes((root / pack / "solution/routine.S").read_bytes())
            elif label == "wrong-call-or-argument":
                before, after = ("mov eax, 1\n", "mov eax, 0\n") if mode == "write" else ("mov r10, rcx\n", "xor r10d, r10d\n")
                text = routine.read_text()
                assert text.count(before) == 1
                routine.write_text(text.replace(before, after, 1))
            elif label == "preserved-register":
                text = routine.read_text()
                assert text.count("    ret\n") == 1
                routine.write_text(text.replace("    ret\n", "    mov rbx, 0\n    ret\n", 1))
            for name in ROLE_FILES:
                if name != "routine.S":
                    assert (directory / name).read_bytes() == (root / pack / role / name).read_bytes()
            run(["cmake", "-S", ".", "-B", "build", "-DCMAKE_BUILD_TYPE=" + build_type, "-DCMAKE_C_COMPILER=" + cc, "-DCMAKE_ASM_COMPILER=" + cc], directory, "configure")
            run(["cmake", "--build", "build", "--verbose", "--parallel", "1"], directory, "build")
            success = label in ("completed", "reference", "release")
            ctest, _ = run(["ctest", "--test-dir", "build", "--output-on-failure"], directory, "ctest", expected=0 if success else None)
            assert ("100% tests passed" in ctest) == success
            trace = directory / "contracts.strace"
            stdout, stderr = run(["strace", "-f", "-yy", "-s", "131072", "-o", str(trace),
                                  str(directory / "build/contracts")], directory, "contracts", expected=0 if success else 1)
            if success:
                assert ("65 byte-exact write cases" if mode == "write" else "three actual creation modes") in stdout
            elif label == "preserved-register":
                assert "preserved=0" in stderr
            app_results = []
            if label != "preserved-register":
                for variant, extra in [("default", []), ("changed", ["--changed"])] if success else [("default", [])]:
                    raw = directory / ("app-" + variant + ".strace")
                    output, _ = run(["strace", "-f", "-yy", "-s", "131072", "-o", str(raw),
                                     str(directory / "build/app"), *extra], directory, "app-" + variant, expected=0 if success else 78)
                    if success and mode == "write":
                        payload = "changed-kernel-bytes" if extra else "owned-kernel-bytes"
                        assert "raw bytes=" + str(len(payload)) + " errno=123 payload=" + payload in output
                        row = re.search(r"short-write requested=(\d+) first=(\d+) full=(-?\d+) remaining=(\d+) total=(\d+) bytes-checked=(\d+)", output)
                        assert row
                        requested, first, full, remaining, total, checked = map(int, row.groups())
                        assert requested == total == checked == first * 2 and remaining == first and full == -errno.EAGAIN
                        assert f"raw-error result={-errno.EBADF} errno=123 libc-error result=-1 errno={errno.EBADF}" in output
                    elif success:
                        wanted = "0400" if extra else "0600"
                        assert "raw-create mode=" + wanted + " requested=" + wanted + " errno=123" in output
                        assert f"raw-existing={-errno.EEXIST} raw-missing={-errno.ENOENT} errno=123 libc-existing=-1 libc-errno={errno.EEXIST}" in output
                    elif mode == "openat":
                        assert "raw-create mode=0000 requested=0600 errno=123" in output
                    app_results.append({"variant": variant, "trace": str(raw.relative_to(args.proof.parent)), "stdout": output})
            obj = directory / "build/CMakeFiles/app.dir/routine.S.o"
            run(["objdump", "-dr", "-Mintel", str(obj)], directory, "routine-disassembly")
            run(["readelf", "-hW", "-sW", str(obj)], directory, "routine-elf")
            if label == "reference":
                trace = ["gdb", "--batch", "--nx", "-q", str(directory / "build/app"),
                         "-ex", "set pagination off", "-ex", "set disassembly-flavor intel",
                         "-ex", "break *" + symbol + "_boundary", "-ex", "run",
                         "-ex", 'printf "ENTER nr=%ld a1=%ld a3=%ld a4=%ld\\n", $rax, $rdi, $rdx, $r10',
                         "-ex", "x/i $rip", "-ex", "si", "-ex", 'printf "RETURN raw=%ld\\n", $rax',
                         "-ex", "disable", "-ex", "continue"]
                output, _ = run(trace, directory, "gdb")
                assert ("ENTER nr=1 " if mode == "write" else "ENTER nr=257 ") in output
                assert "syscall" in output and "exited normally" in output
                assert "RETURN raw=18" in output if mode == "write" else re.search(r"a4=384\b", output) and re.search(r"RETURN raw=\d+", output)
                proof["debuggerTraces"].append({"mode": mode, "path": str((directory / "gdb.stdout.txt").relative_to(args.proof.parent))})
                run([str(directory / "build/app"), "--unknown"], directory, "invalid-arguments", expected=64)
                proof["inputRefusals"].append({"mode": mode, "exitCode": 64})
            proof["profiles"].append({"mode": mode, "label": label, "role": role, "buildType": build_type,
                                      "success": success, "directory": str(directory.relative_to(args.proof.parent)),
                                      "routineObjectSha256": hashlib.sha256(obj.read_bytes()).hexdigest(), "appRuns": app_results})
    assert len(proof["profiles"]) == 12 and sum(row["success"] for row in proof["profiles"]) == 6
    assert len(proof["debuggerTraces"]) == len(proof["inputRefusals"]) == 2
    assert all(hashlib.sha256((root / name).read_bytes()).hexdigest() == sha for name, sha in sources.items())
    proof.update(nativeExecuted=True, sourceUnchanged=True, learnerCompletedOnly="routine.S", commandRecords=records,
                 successfulProfiles=6, unfinishedProfiles=2, controlledWrongCallsOrArguments=2,
                 preservedRegisterRegressions=2, worksheetCompletionNotInferred=True)
    args.proof.write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps({"compiler": args.cc, "nativeExecuted": True, "profiles": 12, "successfulProfiles": 6,
                      "debuggerTraces": 2, "controlledRegressions": 4, "commandRecords": len(records)}))


if __name__ == "__main__":
    main()
