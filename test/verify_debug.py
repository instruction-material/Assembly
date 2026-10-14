"""Verify a real branch fault, one-line repair and before/after debugger evidence."""
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
PACK = ROOT / "ASM-09-unit-10-debugging-at-instruction-level"
parser = argparse.ArgumentParser()
parser.add_argument("--cc", choices=["clang","gcc"], required=True)
parser.add_argument("--skip-debugger", action="store_true")
parser.add_argument("--proof", type=Path, required=True)
args = parser.parse_args()
assert platform.system() == "Linux" and platform.machine() == "x86_64"
args.proof.parent.mkdir(parents=True,exist_ok=True)
process_log = args.proof.with_suffix(".processes.jsonl")
def run(command,cwd,expected=0,input_data=None,timeout=120):
    command = [str(x) for x in command]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    child = subprocess.Popen(command,cwd=cwd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,start_new_session=True)
    cleanup = "process exited"
    try:
        out,err = child.communicate(input=input_data,timeout=timeout)
    except BaseException:
        os.killpg(child.pid,signal.SIGTERM)
        try: out,err = child.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
        cleanup = "child process group terminated"
        raise
    finally:
        with process_log.open("a") as stream:
            stream.write(json.dumps(dict(parentTaskId=os.environ.get("CLASSES_FAMILY_TASK_ID","assembly-debug-native"),
                command=command,cwd=str(cwd),pid=child.pid,startTime=started,
                endTime=datetime.datetime.now(datetime.timezone.utc).isoformat(),exitCode=child.returncode,
                timeoutSeconds=timeout,childProcessGroupCleanup=cleanup))+"\n")
    assert (child.returncode != 0 if expected=="failure" else child.returncode==expected),(command,child.returncode,(out+err).decode(errors="replace"))
    return out,err
def hashes():
    return {str(f.relative_to(PACK)):hashlib.sha256(f.read_bytes()).hexdigest()
        for f in PACK.rglob("*") if f.is_file()}
def expected_index(values,count):
    return next((i for i,x in enumerate(values[:max(0,count)]) if x>=0),-1)
fixed=[[],[-8,-1,4],[-8,0,4],[0],[-1],[-(1<<31)],[(1<<31)-1],
    [-(1<<31),-1,(1<<31)-1],[-1,-2,-3],[-1,1,1],[1,-1],[65535]]
inputs=[(len(row),row) for row in fixed]
state=0x6c38e715ac0294bf
def next_bits():
    global state
    state=(state*6364136223846793005+1442695040888963407)%(1<<64)
    return state
for _ in range(10000):
    count=next_bits()%65
    row=[]
    for _ in range(count):
        bits=next_bits()>>32
        row.append(bits-(1<<32) if bits>=(1<<31) else bits)
    inputs.append((count,row))
inputs.extend((n,[]) for n in [-1,-2,-(1<<63)])
assert len(inputs)==10015
oracle_input="".join(" ".join(map(str,[count,*values,expected_index(values,count)]))+"\n" for count,values in inputs).encode()
expected_contract=b"debug cases passed: 10019\n"
before=hashes()
version=run([args.cc,"--version"],ROOT)[0].decode().splitlines()[0]
profiles,faults,regressions=[],[],[]
assert all("TODO "+key in (PACK/"starter/analysis.md").read_text() for key in ["TARGET","FAILURE","BEFORE","AFTER","REPAIR","CASE","EXPLAIN"])
assert "TODO" not in (PACK/"solution/analysis.md").read_text()
with tempfile.TemporaryDirectory(prefix="assembly-debug-") as work:
    temp=Path(work)
    for role in ["starter","solution"]:shutil.copytree(PACK/role,temp/role)
    shutil.copytree(temp/"starter",temp/"completed")
    file=temp/"completed/routine.S"
    code=file.read_text();assert code.count("    jae debug_found")==1
    file.write_text(code.replace("    jae debug_found","    jge debug_found"))
    for original in (temp/"starter").iterdir():
        if original.name!="routine.S":assert original.read_bytes()==(temp/"completed"/original.name).read_bytes()
    for role in ["starter","solution","completed"]:
        for profile in ["Debug","Release"]:
            build=temp/(role+"-"+profile)
            run(["cmake","-S",temp/role,"-B",build,"-DCMAKE_BUILD_TYPE="+profile,
                "-DCMAKE_C_COMPILER="+args.cc,"-DCMAKE_ASM_COMPILER="+args.cc],temp)
            run(["cmake","--build",build,"--parallel","1"],temp)
            run(["ctest","--test-dir",build,"--output-on-failure"],temp,expected="failure" if role=="starter" else 0)
            out,err=run([build/"assembly_debug"],temp,expected=1 if role=="starter" else 0)
            direct,direct_err=run([build/"debug_contracts"],temp,expected=1 if role=="starter" else 0)
            independent,_=run([build/"debug_contracts","--oracle"],temp,
                expected=1 if role=="starter" else 0,input_data=oracle_input)
            if role=="starter":
                assert out==b"observed=0 expected=2\n" and b"known signed-comparison bug" in err
                assert b"debug index mismatch: observed=0 expected=2" in direct_err
                faults.append(dict(profile=profile,buildSucceeded=True,knownBugReproduced=True,demoExit=1,contractExit=1,observed=0,expected=2))
            else:
                assert out==b"observed=2 expected=2\n" and not err
                assert direct==independent==expected_contract
                profiles.append(dict(role=role,profile=profile,debugCases=10019,
                    independentPythonOracleCases=10015,nativeGuardCases=4,preservedRegisters=6,
                    readonlyInput=True,emptyAndNegativeCountWithoutDereference=True,
                    worksheetCompletionNotInferred=True,demoOutput=out.decode()))
    reference=(temp/"solution/routine.S").read_text()
    mutations={
        "unsigned-branch":reference.replace("    jge debug_found","    jae debug_found"),
        "strict-positive":reference.replace("    jge debug_found","    jg debug_found"),
        "wrong-data-width":reference.replace("    cmp r8d, 0","    cmp r8, 0"),
        "skipped-first-index":reference.replace("    xor ecx, ecx","    mov ecx, 1"),
        "one-past-count":reference.replace("    jge .Ldebug_missing","    jg .Ldebug_missing"),
        "preserved-register":reference.replace("debug_first_nonnegative:\n","debug_first_nonnegative:\n    mov rbx, 1\n"),
        "missing-result-width":reference.replace("    mov rax, -1","    mov eax, -1")
    }
    for kind,mutant in mutations.items():
        assert mutant!=reference
        folder=temp/kind;shutil.copytree(temp/"solution",folder)
        (folder/"routine.S").write_text(mutant)
        run([args.cc,"-std=c17","-O1","-Wall","-Wextra","-Wpedantic","-Wconversion","-Werror",
            "tests.c","abi_checks.S","routine.S","-o","broken"],folder)
        _,error=run([folder/"broken"],folder,expected="failure")
        if kind=="preserved-register":assert b"callee-saved register contract failed" in error
        regressions.append(dict(kind=kind,rejected=True))
    debugger=dict(status="not exercised in emulated local run")
    if not args.skip_debugger:
        traces={}
        for role,next_symbol,result in [("starter","debug_found",0),("completed","debug_advance",2)]:
            trace,_=run(["gdb","--batch","--nx","-q",temp/(role+"-Debug")/"assembly_debug",
                "-ex","set disassembly-flavor intel","-ex","tbreak *debug_branch_decision","-ex","run",
                "-ex",'printf "DEBUG-before index=%lld value=%d\\n", $rcx, (int)$r8',
                "-ex",'printf "DEBUG-flags SF=%d OF=%d ZF=%d CF=%d\\n", (int)(($eflags>>7)&1), (int)(($eflags>>11)&1), (int)(($eflags>>6)&1), (int)($eflags&1)',
                "-ex","si","-ex",'printf "DEBUG-after-branch\\n"',"-ex","x/i $pc",
                "-ex","finish","-ex",'printf "DEBUG-result=%lld\\n", $rax',"-ex","continue"],temp)
            assert b"DEBUG-before index=0 value=-8" in trace
            assert b"DEBUG-flags SF=1 OF=0 ZF=0 CF=0" in trace
            after=trace.split(b"DEBUG-after-branch\n",1)[1].split(b"\n",1)[0]
            assert ("<"+next_symbol+">").encode() in after,after
            assert ("DEBUG-result="+str(result)).encode() in trace
            traces[role]=trace.decode()
        debugger=dict(status="accepted",faultyAndCorrectedSingleStep=True,traces=traces)
    disassembly=run(["objdump","-d","-M","intel",temp/"solution-Debug/assembly_debug"],temp)[0]
    assert b"<debug_first_nonnegative>:" in disassembly and b"<debug_branch_decision>:" in disassembly
assert not Path(work).exists() and before==hashes()
receipt=dict(event="verified-assembly-debug",compiler=args.cc,compilerVersion=version,
    acceptedProfiles=profiles,originalFaultProfiles=faults,controlledRegressions=regressions,
    independentLearnerCompletedOnly="routine.S",starterWorksheetUnchanged=True,
    independentOracle="Python signed comparison and first-index enumeration",
    debugger=debugger,sourceFilesUnchanged=True,temporaryBuildCleanup=True)
args.proof.write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps(dict(event=receipt["event"],compiler=args.cc,debugCases=sum(x["debugCases"] for x in profiles),
    faultProfiles=len(faults),acceptedProfiles=len(profiles),regressionsRejected=len(regressions),debugger=debugger["status"])))
