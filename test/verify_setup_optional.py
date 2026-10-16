"""Exercise actual object/link boundaries and assembly preprocessing with native tools."""
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

PACKS = {"symbols": "ASM-01-asm0-setup-and-tooling-supplemental-2",
         "preprocess": "ASM-02-asm0-setup-and-tooling-supplemental-3"}
ROLE_FILES = ("main.c", "routine.S", "lab.h", "tests.c", "CMakeLists.txt", "trace.md")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", choices=("clang", "gcc"), required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    ast.parse(Path(__file__).read_text(), feature_version=(3, 10))
    root = Path(__file__).resolve().parents[1]
    source_hashes = {}
    for mode, pack in PACKS.items():
        changed = []
        for name in ROLE_FILES:
            a, b = [(root / pack / role / name).read_bytes() for role in ("starter", "solution")]
            if a != b:
                changed.append(name)
        assert changed == (["routine.S"] if mode == "symbols" else ["CMakeLists.txt"])
        for path in sorted((root / pack).rglob("*")):
            if path.is_file():
                source_hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert len(source_hashes) == 26
    proof = {"sourceFiles": source_hashes, "compiler": args.cc, "nativeExecuted": False, "profiles": []}
    args.proof.parent.mkdir(parents=True, exist_ok=True)
    if args.source_only:
        args.proof.write_text(json.dumps(proof, indent=2) + "\n")
        print("Source parity checked; native acceptance not executed")
        return
    assert sys.platform == "linux" and platform.machine().lower() in ("x86_64", "amd64")
    cc = shutil.which(args.cc)
    assert cc and all(shutil.which(x) for x in ("cmake", "ctest", "nm", "readelf", "objdump"))
    work = args.proof.parent / (args.proof.stem + "-raw")
    work.mkdir(exist_ok=False)
    records = []

    def run(argv, cwd, label, expected=0):
        started = time.time()
        process = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        record = {"parentTask": "assembly-setup-optional-native", "parentPid": os.getpid(),
                  "pid": process.pid, "cwd": str(cwd), "command": argv,
                  "startTime": started, "timeoutSeconds": 90}
        logs = args.proof.with_suffix(".processes.jsonl")
        with logs.open("a") as out:
            out.write(json.dumps(dict(record, event="start")) + "\n")
        cleanup = "not needed"
        try:
            stdout, stderr = process.communicate(timeout=90)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                stdout, stderr = process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
            cleanup = "owned process group terminated and reaped"
            raise
        finally:
            record.update(endTime=time.time(), exitCode=process.returncode, childProcessGroupCleanup=cleanup)
            with logs.open("a") as out:
                out.write(json.dumps(dict(record, event="end")) + "\n")
        prefix = cwd / label
        prefix.with_suffix(".stdout.txt").write_bytes(stdout)
        prefix.with_suffix(".stderr.txt").write_bytes(stderr)
        records.append(record)
        assert process.returncode == expected if expected is not None else process.returncode != 0, (label, process.returncode, stderr.decode(errors="replace"))
        return stdout.decode(), stderr.decode(), process.returncode

    version, _, _ = run([cc, "--version"], work, "compiler-version")
    proof["compilerVersion"] = version
    for mode, pack in PACKS.items():
        default = 42 if mode == "symbols" else 41
        for label, role, success, value in [("untouched", "starter", False, default),
                                           ("completed", "starter", True, default),
                                           ("reference", "solution", True, default),
                                           ("changed-value", "solution", True, 73),
                                           ("controlled-regression", "solution", False, default),
                                           ("invalid-value", "solution", None, 256)]:
            directory = work / (mode + "-" + label)
            shutil.copytree(root / pack / role, directory)
            if label in ("completed", "controlled-regression"):
                if mode == "symbols":
                    path = directory / "routine.S"
                    before, after = ("# TODO: export lab_answer to the separately compiled C caller", ".globl lab_answer") if label == "completed" else (".globl lab_answer", "# deliberately local regression")
                else:
                    path = directory / "CMakeLists.txt"
                    before, after = ('set(LAB_ASM_LANGUAGE "assembler"', 'set(LAB_ASM_LANGUAGE "assembler-with-cpp"') if label == "completed" else ('set(LAB_ASM_LANGUAGE "assembler-with-cpp"', 'set(LAB_ASM_LANGUAGE "assembler"')
                text = path.read_text()
                assert text.count(before) == 1
                path.write_text(text.replace(before, after, 1))
            build = directory / "build"
            configure = ["cmake", "-S", ".", "-B", "build", "-DCMAKE_BUILD_TYPE=Debug", "-DCMAKE_C_COMPILER=" + cc, "-DCMAKE_ASM_COMPILER=" + cc, "-DLAB_VALUE=" + str(value)]
            if label == "invalid-value":
                run(configure, directory, "configure", expected=None)
                assert not (build / "app").exists()
                proof["profiles"].append({"mode": mode, "label": label, "role": role,
                                          "configurationRefused": True,
                                          "directory": str(directory.relative_to(args.proof.parent))})
                continue
            run(configure, directory, "configure")
            run(["cmake", "--build", "build", "--parallel", "1", "--verbose"], directory, "cmake-build", expected=0 if success else None)
            commands = json.loads((build / "compile_commands.json").read_text())
            asm_commands = [x["command"] for x in commands if x["file"].endswith("routine.S")]
            assert len(asm_commands) == 2
            language = "assembler-with-cpp"
            if mode == "preprocess":
                language = re.search(r'set\(LAB_ASM_LANGUAGE "([^"]+)"', (directory / "CMakeLists.txt").read_text()).group(1)
                assert all("-x " + language in command for command in asm_commands)
            run([cc, "-std=c17", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "-DLAB_VALUE=" + str(value), "-c", "main.c", "-o", "main.o"], directory, "compile-caller")
            run([cc, "-DLAB_VALUE=" + str(value), "-x", language, "-c", "routine.S", "-o", "routine.o"], directory, "assemble-routine")
            preprocessed, _, _ = run([cc, "-DLAB_VALUE=" + str(value), "-E", "-P", "-x", "assembler-with-cpp", "routine.S"], directory, "diagnostic-preprocess")
            assert re.search(r"movl\s+\$" + str(value) + r",\s*%eax", preprocessed)
            caller, _, _ = run(["nm", "-P", "main.o"], directory, "caller-symbols")
            symbols, _, _ = run(["nm", "-P", "routine.o"], directory, "routine-symbols")
            run(["readelf", "-Ws", "routine.o"], directory, "elf-symbols")
            relocations, _, _ = run(["readelf", "-r", "routine.o"], directory, "relocations")
            disassembly, _, _ = run(["objdump", "-dr", "-Mintel", "routine.o"], directory, "disassembly")
            assert re.search(r"^lab_answer U\b", caller, re.MULTILINE)
            binding = "T" if success or mode == "preprocess" else "t"
            assert re.search(r"^lab_answer " + binding + r"\b", symbols, re.MULTILINE)
            unresolved_macro = mode == "preprocess" and not success
            assert bool(re.search(r"^LAB_VALUE U\b", symbols, re.MULTILINE)) == unresolved_macro
            assert ("LAB_VALUE" in relocations) == unresolved_macro
            _, diagnostic, _ = run([cc, "main.o", "routine.o", "-o", "staged-app"], directory, "link-stages", expected=0 if success else None)
            if success:
                expected = "answer=" + str(value) + "\n"
                stdout, _, _ = run([str((directory / "staged-app").resolve())], directory, "run-stages")
                assert stdout == expected
                stdout, _, _ = run([str((build / "app").resolve())], directory, "run-cmake")
                assert stdout == expected
                run(["ctest", "--test-dir", "build", "--output-on-failure"], directory, "contracts")
                assert re.search(r"mov\s+eax,0x" + format(value, "x") + r"\b", disassembly)
            else:
                assert ("LAB_VALUE" if unresolved_macro else "lab_answer") in diagnostic
                assert not (directory / "staged-app").exists() and not (build / "app").exists()
            retained = {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in (directory / "main.o", directory / "routine.o")}
            proof["profiles"].append({"mode": mode, "label": label, "role": role,
                                      "value": value, "success": success,
                                      "binding": binding, "unresolvedMacro": unresolved_macro,
                                      "objects": retained,
                                      "directory": str(directory.relative_to(args.proof.parent))})
    assert len(proof["profiles"]) == 12
    assert sum(x.get("success") is True for x in proof["profiles"]) == 6
    assert sum(x.get("success") is False for x in proof["profiles"]) == 4
    assert sum(x.get("configurationRefused") is True for x in proof["profiles"]) == 2
    assert all(hashlib.sha256((root / path).read_bytes()).hexdigest() == sha for path, sha in source_hashes.items())
    proof.update(nativeExecuted=True, sourceUnchanged=True, commandRecords=records,
                 nativeSuccessfulProfiles=6, actualLinkFailures=4, configurationRefusals=2,
                 diagnosticPreprocessingIsSeparateFromSelectedBuild=True)
    args.proof.write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps({"compiler":args.cc,"nativeExecuted":True,"successful":6,"linkFailures":4,"configurationRefusals":2,"commandRecords":len(records)}))


if __name__ == "__main__":
    main()
