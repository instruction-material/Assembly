"""Verify the nested assembly calls and the balanced stack-frame contract."""
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
PACK = ROOT / "ASM-07-unit-5-the-stack-and-function-calls"
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
            stream.write(json.dumps(dict(parentTaskId=os.environ.get("CLASSES_FAMILY_TASK_ID", "assembly-stack-native"),
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

def oracle(a, b):
    return signed((2 * a + 5) + (2 * b + 5))

inputs = [(0,0),(3,7),(-5,19),(-1,-1),((1<<63)-1,1),(-(1<<63),-1),
          (-(1<<63),(1<<63)-1),((1<<63)-1,(1<<63)-1),(-(1<<63),-(1<<63)),
          (1<<32,-7),(-7,1<<32),(41,-80)]
state = 0x312fa56c70b981d4
for _ in range(10000):
    state = (state * 6364136223846793005 + 1442695040888963407) % (1<<64)
    a = signed(state)
    state = (state * 6364136223846793005 + 1442695040888963407) % (1<<64)
    inputs.append((a,signed(state)))
assert len(inputs) == 10012
oracle_input = "".join(f"{a} {b} {oracle(a,b)}\n" for a,b in inputs).encode()
demo_pairs = [(3,7),(-5,19),((1<<63)-1,1),(-(1<<63),-1)]
expected_demo = "".join(f"a={a} b={b} result={oracle(a,b)}\n" for a,b in demo_pairs).encode()
expected_contract = b"stack cases passed: 10012\n"
before = hashes()
version = run([args.cc,"--version"],ROOT)[0].decode().splitlines()[0]
profiles, unfinished, regressions = [],[],[]
with tempfile.TemporaryDirectory(prefix="assembly-stack-") as work:
    temp = Path(work)
    for role in ["starter","solution"]:
        shutil.copytree(PACK / role,temp / role)
    shutil.copytree(temp / "starter",temp / "completed")
    routine = temp / "completed/routine.S"
    code = routine.read_text()
    old = """    /* TODO STACK_CALLS: call stack_leaf for a, then b; keep b and the first
       result across calls, align the call sites and restore all saved state. */
    xor eax, eax
    ret"""
    learner = """    push rbp
    push rbx
    push r12
    mov rbx, rsi
    call stack_leaf
    mov r12, rax
    mov rdi, rbx
    call stack_leaf
    add rax, r12
    pop r12
    pop rbx
    pop rbp
    ret"""
    assert code.count(old) == 1
    routine.write_text(code.replace(old,learner))
    for f in (temp / "starter").iterdir():
        if f.name != "routine.S":
            assert f.read_bytes() == (temp / "completed" / f.name).read_bytes()
    for role in ["starter","solution","completed"]:
        for profile in ["Debug","Release"]:
            build = temp / (role + "-" + profile)
            run(["cmake","-S",temp / role,"-B",build,"-DCMAKE_BUILD_TYPE="+profile,
                 "-DCMAKE_C_COMPILER="+args.cc,"-DCMAKE_ASM_COMPILER="+args.cc],temp)
            run(["cmake","--build",build,"--parallel","1"],temp)
            run(["ctest","--test-dir",build,"--output-on-failure"],temp,
                expected="failure" if role=="starter" else 0)
            output,error = run([build / "assembly_stack"],temp,expected=78 if role=="starter" else 0)
            direct,_ = run([build / "stack_contracts"],temp,expected=1 if role=="starter" else 0)
            independent,_ = run([build / "stack_contracts","--oracle"],temp,
                expected=1 if role=="starter" else 0,input_data=oracle_input)
            if role=="starter":
                assert not output and b"unfinished or incorrect" in error
                unfinished.append(dict(profile=profile,demoExit=78,contractExit=1))
            else:
                assert output==expected_demo and not error
                assert direct==independent==expected_contract
                profiles.append(dict(role=role,profile=profile,stackCases=10012,
                    independentPythonOracleCases=10012,preservedRegisters=6,
                    actualLeafCallsPerInvocation=2,orderedArgumentsVerified=True,
                    leafEntryStackRemainder=8,callerSavedRegistersClobbered=True,
                    demoOutput=output.decode()))
    reference = (temp / "solution/routine.S").read_text()
    begin = reference.index("stack_pair:\n") + len("stack_pair:\n")
    end = reference.index(".size stack_pair",begin)
    mutations = {
        "numeric-shortcut": reference[:begin]+"    lea rax, [rdi + rsi]\n    lea rax, [rax + rax + 10]\n    ret\n"+reference[end:],
        "wrong-second-argument": reference.replace("    mov rbx, rsi","    mov rbx, rdi"),
        "lost-first-result": reference.replace("    mov r12, rax","    mov r12, 0"),
        "stack-alignment": reference.replace("    sub rsp, 8","    sub rsp, 16").replace("    add rsp, 8","    add rsp, 16"),
        "preserved-register": reference.replace("    pop rbx","    add rsp, 8"),
        "result-width": reference.replace("    lea rax, [rdi + rdi + 5]","    lea eax, [rdi + rdi + 5]"),
        "wrong-leaf-offset": reference.replace("    lea rax, [rdi + rdi + 5]","    lea rax, [rdi + rdi + 6]")
    }
    for kind,mutant in mutations.items():
        assert mutant!=reference
        folder=temp/kind
        shutil.copytree(temp/"solution",folder)
        (folder/"routine.S").write_text(mutant)
        run([args.cc,"-std=c17","-O1","-Wall","-Wextra","-Wpedantic","-Wconversion","-Werror",
             "-DSTACK_TEST_PROBE","tests.c","abi_checks.S","routine.S","-o","broken"],folder)
        _,error=run([folder/"broken"],folder,expected="failure")
        if kind=="preserved-register":
            assert b"callee-saved register contract failed" in error
        regressions.append(dict(kind=kind,rejected=True))
    disassembly=run(["objdump","-d","-M","intel",temp/"solution-Debug/assembly_stack"],temp)[0]
    assert b"<stack_pair>:" in disassembly and b"<stack_leaf>:" in disassembly
    debugger=dict(status="not exercised in emulated local run")
    if not args.skip_debugger:
        trace,_=run(["gdb","--batch","--nx","-q",temp/"solution-Debug/assembly_stack",
            "-ex","set disassembly-flavor intel","-ex","tbreak *stack_leaf","-ex","run",
            "-ex",'printf "STACK-input=%lld\\n", $rdi',
            "-ex",'printf "STACK-entry-rem=%lu\\n", ((unsigned long)$rsp & 15)',
            "-ex","finish","-ex",'printf "STACK-leaf=%lld\\n", $rax',"-ex","continue"],temp)
        assert b"STACK-input=3" in trace and b"STACK-entry-rem=8" in trace and b"STACK-leaf=11" in trace
        assert b"a=3 b=7 result=30" in trace
        debugger=dict(status="accepted",trace=trace.decode())
assert not Path(work).exists() and before==hashes()
receipt=dict(event="verified-assembly-stack",compiler=args.cc,compilerVersion=version,
    acceptedProfiles=profiles,unfinishedProfilesRejected=unfinished,controlledRegressions=regressions,
    independentLearnerCompletedOnly="routine.S",independentOracle="Python arbitrary-precision arithmetic",
    debugger=debugger,sourceFilesUnchanged=True,temporaryBuildCleanup=True)
args.proof.write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps(dict(event=receipt["event"],compiler=args.cc,stackCases=sum(p["stackCases"] for p in profiles),
    acceptedProfiles=len(profiles),regressionsRejected=len(regressions),debugger=debugger["status"])))

