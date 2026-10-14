"""Verify the working compiler baseline, actual output and optimization equivalence."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "ASM-08-unit-9-reading-compiler-output"
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
            stream.write(json.dumps(dict(parentTaskId=os.environ.get("CLASSES_FAMILY_TASK_ID", "assembly-compiler-native"),
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
    bits=number % (1<<64)
    return bits-(1<<64) if bits >= (1<<63) else bits

def oracle(value,factor,bias):
    return signed(value*factor+bias)

inputs=[(0,0,0),(6,7,-5),(-9,3,1),((1<<63)-1,2,7),(-(1<<63),-1,0),
        (-(1<<63),0,(1<<63)-1),((1<<63)-1,(1<<63)-1,-(1<<63)),
        (-(1<<63),-(1<<63),(1<<63)-1),((1<<63)-1,1,0),(1<<32,1<<32,1),
        (-(1<<32),3,-7),(3,-(1<<32),1<<32),(1,0,-1)]
state=0x4bc392e105a67d8f
for _ in range(10000):
    state=(state*6364136223846793005+1442695040888963407)%(1<<64);v=signed(state)
    state=(state*6364136223846793005+1442695040888963407)%(1<<64);f=signed(state)
    state=(state*6364136223846793005+1442695040888963407)%(1<<64)
    inputs.append((v,f,signed(state)))
assert len(inputs)==10013
oracle_input="".join(f"{v} {f} {b} {oracle(v,f,b)}\n" for v,f,b in inputs).encode()
demo_inputs=[(6,7,-5),(-9,3,1),((1<<63)-1,2,7),(-(1<<63),-1,0)]
expected_demo="".join(f"value={v} factor={f} bias={b} result={oracle(v,f,b)}\n" for v,f,b in demo_inputs).encode()
expected_contract=b"compiler cases passed: 10013\n"
before=hashes()
version=run([args.cc,"--version"],ROOT)[0].decode().splitlines()[0]
starter_worksheet=(PACK/"starter/analysis.md").read_text()
assert all("TODO "+key in starter_worksheet for key in ["TARGET","PREDICT","MAP","COMPARE","CASE","TRACE","EXPLAIN"])
assert "TODO" not in (PACK/"solution/analysis.md").read_text()
assert (PACK/"starter/model.c").read_bytes()==(PACK/"solution/model.c").read_bytes()
profiles,generated,regressions=[],[],[]
retained=args.proof.parent/("compiler-"+args.cc+"-generated")
retained.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="assembly-compiler-") as work:
    temp=Path(work)
    for role in ["starter","solution"]:
        shutil.copytree(PACK/role,temp/role)
        for profile,opt in [("Debug","-O0"),("Release","-O2")]:
            build=temp/(role+"-"+profile)
            flag="-DCMAKE_C_FLAGS_DEBUG=-O0 -g" if profile=="Debug" else "-DCMAKE_C_FLAGS_RELEASE=-O2 -g -DNDEBUG"
            run(["cmake","-S",temp/role,"-B",build,"-DCMAKE_BUILD_TYPE="+profile,
                 "-DCMAKE_C_COMPILER="+args.cc,"-DCMAKE_ASM_COMPILER="+args.cc,flag],temp)
            run(["cmake","--build",build,"--parallel","1"],temp)
            run(["ctest","--test-dir",build,"--output-on-failure"],temp)
            output,error=run([build/"assembly_compiler"],temp)
            assert output==expected_demo and not error
            assert run([build/"compiler_contracts"],temp)[0]==expected_contract
            assert run([build/"compiler_contracts","--oracle"],temp,input_data=oracle_input)[0]==expected_contract
            profiles.append(dict(role=role,profile=profile,optimization=opt,compilerCases=10013,
                independentPythonOracleCases=10013,preservedRegisters=6,workingBaseline=True,
                worksheetCompletionNotInferred=True,demoOutput=output.decode()))
            assembly=temp/(role+"-"+opt.removeprefix("-")+".s")
            run([args.cc,"-std=c17",opt,"-g","-S","-masm=intel","-fverbose-asm","model.c","-o",assembly],temp/role)
            code=assembly.read_text()
            assert ".intel_syntax" in code and "compiled_score:" in code
            executable=temp/(role+"-"+opt.removeprefix("-")+"-generated")
            run([args.cc,"-std=c17","-Wall","-Wextra","-Wpedantic","-Wconversion","-Werror",
                 "tests.c","abi_checks.S",assembly,"-o",executable],temp/role)
            assert run([executable,"--oracle"],temp,input_data=oracle_input)[0]==expected_contract
            disassembly=run(["objdump","-d","--no-show-raw-insn","-M","intel",executable],temp)[0].decode()
            match=re.search(r"<compiled_score>:\n(.*?)(?:\n\n|\Z)",disassembly,re.S)
            assert match
            instructions=[m.group(1) for line in match.group(1).splitlines() if (m:=re.match(r"\s*[0-9a-f]+:\s+(.+)",line))]
            assert instructions
            assembly_name=role+"-"+opt.removeprefix("-")+".s"
            linked_name=role+"-"+opt.removeprefix("-")+"-linked.txt"
            (retained/assembly_name).write_text(code)
            (retained/linked_name).write_text(disassembly)
            generated.append(dict(role=role,optimization=opt,assemblyFile=assembly_name,
                assemblySha256=hashlib.sha256(code.encode()).hexdigest(),linkedFile=linked_name,
                linkedSha256=hashlib.sha256(disassembly.encode()).hexdigest(),instructions=instructions,
                assembledAndExecuted=True,independentOracleCases=10013))
    for role in ["starter","solution"]:
        records=[r for r in generated if r["role"]==role]
        assert len(records)==2 and records[0]["instructions"]!=records[1]["instructions"]
    reference=(temp/"solution/model.c").read_text()
    mutations={
        "value-width":reference.replace("(uint64_t)value","(uint64_t)(uint32_t)value"),
        "factor-width":reference.replace("(uint64_t)factor","(uint64_t)(uint32_t)factor"),
        "missing-bias":reference.replace("+ (uint64_t)bias","+ (uint64_t)bias * UINT64_C(0)"),
        "bias-sign":reference.replace("+ (uint64_t)bias","- (uint64_t)bias"),
        "output-width":reference.replace("return result;","return (int64_t)(uint32_t)result;"),
        "signed-overflow":'''#include "model.h"
int64_t compiled_score(int64_t value,int64_t factor,int64_t bias) {
    return value*factor+bias;
}
'''
    }
    for kind,code in mutations.items():
        assert code!=reference
        folder=temp/kind
        shutil.copytree(temp/"solution",folder)
        (folder/"model.c").write_text(code)
        run([args.cc,"-std=c17","-O1","-Wall","-Wextra","-Wpedantic","-Wconversion","-Werror",
             "-fsanitize=undefined","-fno-sanitize-recover=undefined","tests.c","abi_checks.S","model.c","-o","broken"],folder)
        _,error=run([folder/"broken"],folder,expected="failure")
        if kind=="signed-overflow":assert b"runtime error" in error
        regressions.append(dict(kind=kind,rejected=True))
    debugger=dict(status="not exercised in emulated local run")
    if not args.skip_debugger:
        trace,_=run(["gdb","--batch","--nx","-q",temp/"starter-Debug/assembly_compiler",
            "-ex","set disassembly-flavor intel","-ex","tbreak *compiled_score","-ex","run",
            "-ex",'printf "COMPILER-inputs=%lld,%lld,%lld\\n", $rdi, $rsi, $rdx',
            "-ex","finish","-ex",'printf "COMPILER-result=%lld\\n", $rax',"-ex","continue"],temp)
        assert b"COMPILER-inputs=6,7,-5" in trace and b"COMPILER-result=37" in trace
        assert b"value=-9 factor=3 bias=1 result=-26" in trace
        debugger=dict(status="accepted",trace=trace.decode())
assert not Path(work).exists() and before==hashes()
receipt=dict(event="verified-assembly-compiler",compiler=args.cc,compilerVersion=version,
    acceptedProfiles=profiles,generatedAssembly=generated,controlledRegressions=regressions,
    workingStarterAndReference=True,starterWorksheetUnchanged=True,
    independentOracle="Python arbitrary-precision multiplication and modular bit interpretation",
    optimizationInstructionShapesDiffer=True,debugger=debugger,sourceFilesUnchanged=True,
    temporaryBuildCleanup=True)
args.proof.write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps(dict(event=receipt["event"],compiler=args.cc,compilerCases=sum(p["compilerCases"] for p in profiles),
    acceptedProfiles=len(profiles),generatedAssemblyExecuted=len(generated),regressionsRejected=len(regressions),
    debugger=debugger["status"])))

