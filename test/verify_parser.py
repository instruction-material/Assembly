"""Verify the parser's native contract and complete learner edits."""
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
PACK = ROOT / "ASM5-Tiny-Command-Line-Parser"
parser = argparse.ArgumentParser()
parser.add_argument("--cc", choices=["clang", "gcc"], required=True)
parser.add_argument("--skip-debugger", action="store_true")
parser.add_argument("--proof", type=Path, default=Path("output/parser-proof.json"))
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
expected_default = b"sum=15\nmax=12\nxor=-9\n"
invalid_cli = [
 ["sum"], ["sum","1"], ["bad","1","2"], ["SUM","1","2"],
 ["sum","","2"], ["sum","+","2"], ["sum","-","2"], ["sum"," 1","2"],
 ["sum","1 ","2"], ["sum","1x","2"], ["sum","1.0","2"], ["sum","0x10","2"],
 ["sum","9223372036854775808","0"], ["sum","-9223372036854775809","0"],
 ["sum","18446744073709551616","0"], ["sum","1","2","3x"]
]
valid_cli = [
 (["sum","12","-4","7"],15), (["max","12","-4","7"],12), (["xor","12","-4","7"],-9),
 (["sum","9223372036854775807","1"],-9223372036854775808),
 (["sum","-9223372036854775808","-1"],9223372036854775807),
 (["sum","-9223372036854775808","-9223372036854775808"],0),
 (["max","-5","-9"],-5), (["max","-9223372036854775808","9223372036854775807"],9223372036854775807),
 (["xor","9223372036854775807","-1"],-9223372036854775808),
 (["sum","+0001","-0002"],-1), (["sum","4294967296","1"],4294967297)
]
with tempfile.TemporaryDirectory(prefix="assembly-parser-") as work:
    temp = Path(work)
    for role in ["starter","solution"]:
        shutil.copytree(PACK / role, temp / role)
    shutil.copytree(temp / "starter", temp / "completed")
    path = temp / "completed/parser.S";code=path.read_text()
    markers = {
        "    /* TODO PARSE_SIGN: accept optional +/-, update index, negative flag\n       and final allowed digit (7 for positive, 8 for negative). */\n    nop":
        """    cmp BYTE PTR [rdi], '-'
    je .Llearner_negative
    cmp BYTE PTR [rdi], '+'
    jne .Llearner_sign_done
    inc rcx
    jmp .Llearner_sign_done
.Llearner_negative:
    inc rcx
    mov r9d, 1
    mov r11d, 8
.Llearner_sign_done:""",
        "    /* TODO PARSE_BOUND: reject a magnitude that would exceed the signed\n       limit before multiplying by 10 or adding the current digit. */\n    nop":
        """    cmp r10, rax
    jb .Lparse_fail
    jne .Ldigit_fits
    cmp r11d, edx
    jb .Lparse_fail"""
    }
    for old,new in markers.items():
        assert code.count(old)==1;code=code.replace(old,new)
    path.write_text(code)
    for p in (temp/"starter").iterdir():
        if p.name!="parser.S":assert p.read_bytes()==(temp/"completed"/p.name).read_bytes()
    for role in ["starter","solution","completed"]:
        for profile in ["Debug","Release"]:
            build=temp/(role+"-"+profile)
            run(["cmake","-S",temp/role,"-B",build,"-DCMAKE_BUILD_TYPE="+profile,
                 "-DCMAKE_C_COMPILER="+args.cc,"-DCMAKE_ASM_COMPILER="+args.cc],temp)
            run(["cmake","--build",build,"--parallel","1"],temp)
            run(["ctest","--test-dir",build,"--output-on-failure"],temp,expected="failure" if role=="starter" else 0)
            exe=build/"assembly_parser";out,err=run([exe],temp,expected=78 if role=="starter" else 0)
            contracts,contract_err=run([build/"parser_contracts"],temp,expected=1 if role=="starter" else 0)
            for argv in invalid_cli:
                cli_out,cli_err=run([exe,*argv],temp,expected=2)
                assert not cli_out and b"signed decimal 64-bit" in cli_err
            for argv,value in valid_cli:
                cli_out,cli_err=run([exe,*argv],temp,expected=78 if role=="starter" else 0)
                if role=="starter":assert not cli_out and b"unfinished or incorrect" in cli_err
                else:assert cli_out==("result="+str(value)+"\n").encode() and not cli_err
            if role=="starter":
                assert not out and b"unfinished or incorrect" in err and b"expected success=" in contract_err
                rejected.append(dict(profile=profile,demoExit=78,contractExit=1,invalidCliRejected=len(invalid_cli)))
            else:
                assert out==expected_default and not err
                count=re.fullmatch(rb"(\d+) parse cases and (\d+) equality cases accepted; outputs and bounds verified\n",contracts)
                assert count and int(count[1])==8056 and int(count[2])==1101 and not contract_err
                profiles.append(dict(role=role,profile=profile,parserCases=9157,parseCases=8056,equalityCases=1101,
                    preservedRegisters=6,guardedInputsAndOutput=True,outputUnchangedOnFailure=True,
                    invalidCliRejected=len(invalid_cli),validCliAccepted=len(valid_cli),demoOutput=out.decode()))
    mutations={
        "sign-limit":("parser.S","    mov r11d, 8","    mov r11d, 7"),
        "no-magnitude-bound":("parser.S","    cmp rax, r10\n    ja .Lparse_fail","    cmp rax, r10\n    nop"),
        "wrong-final-digit":("parser.S","    cmp edx, r11d\n    ja .Lparse_fail","    cmp edx, r11d\n    nop"),
        "failure-writes-output":("parser.S",".Lparse_fail:\n",".Lparse_fail:\n    mov QWORD PTR [r8], 0\n"),
        "prefix-equality":("parser.S","    jne .Lstreq_no","    jne .Lstreq_yes"),
        "preserved-register":("parser.S","asm_parse_i64:\n","asm_parse_i64:\n    mov rbx, 0\n"),
        "input-overread":("parser.S",".Lapply_sign:\n",".Lapply_sign:\n    mov dl, BYTE PTR [rdi + rcx + 1]\n")
    }
    for name,(filename,old,new) in mutations.items():
        folder=temp/name;shutil.copytree(temp/"solution",folder);path=folder/filename;code=path.read_text();assert code.count(old)==1;path.write_text(code.replace(old,new))
        run([args.cc,"-std=c17","-Wall","-Wextra","-Wpedantic","-Wconversion","-Werror",
             "tests.c","abi_checks.S","parser.S","-o","broken"],folder)
        _,err=run([folder/"broken"],folder,expected="failure")
        if name=="preserved-register":assert b"callee-saved register contract failed" in err
        regressions.append(dict(kind=name,rejected=True))
    disassembly,_=run(["objdump","-d","-M","intel",temp/"solution-Debug/assembly_parser"],temp)
    assert b"<asm_parse_i64>:" in disassembly and b"<asm_streq>:" in disassembly
    debugger=dict(status="not exercised in emulated local run")
    if not args.skip_debugger:
        trace,_=run(["gdb","--batch","--nx","-q",temp/"solution-Debug/assembly_parser",
            "-ex","set disassembly-flavor intel","-ex","tbreak *asm_parse_i64","-ex","run",
            "-ex","x/s $rdi","-ex","set $saved_output = (long long *)$rsi","-ex","finish",
            "-ex",'printf "PARSER-success=%d\\n", $eax',
            "-ex",'printf "PARSER-output=%lld\\n", *$saved_output',"-ex","continue"],temp)
        assert b'"-1"' in trace and b"PARSER-success=1" in trace and b"PARSER-output=-1" in trace
        assert b"sum=15" in trace and b"xor=-9" in trace
        debugger=dict(status="accepted",trace=trace.decode())
assert not Path(work).exists() and before==hashes()
receipt=dict(event="verified-assembly-parser",compiler=args.cc,compilerVersion=version,
    acceptedProfiles=profiles,unfinishedProfilesRejected=rejected,controlledRegressions=regressions,
    independentLearnerCompletedOnly="parser.S",debugger=debugger,sourceFilesUnchanged=True,temporaryBuildCleanup=True)
args.proof.write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps(dict(event=receipt["event"],compiler=args.cc,parserCases=sum(p["parserCases"] for p in profiles),
    acceptedProfiles=len(profiles),regressionsRejected=len(regressions),debugger=debugger["status"])))
