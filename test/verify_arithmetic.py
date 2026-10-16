"""Verify actual arithmetic flags, implicit operands, guarded faults and listings."""
import argparse
import datetime
import hashlib
import json
import os
import platform
import re
import resource
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'ASM-06-unit-3-arithmetic-and-logic'
parser = argparse.ArgumentParser()
parser.add_argument('--cc', choices=['clang', 'gcc'], required=True)
parser.add_argument('--proof', type=Path, required=True)
args = parser.parse_args()
assert platform.system() == 'Linux' and platform.machine() == 'x86_64'
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
args.proof = args.proof.resolve()
args.proof.parent.mkdir(parents=True, exist_ok=True)
log = args.proof.with_suffix('.processes.jsonl')
MASK = (1 << 64) - 1
SIGN = 1 << 63
CF, ZF, SF, OF = 1, 64, 128, 2048
ALL = CF | ZF | SF | OF
SENTINEL = int('a5' * 8, 16)


def run(argv, cwd, expected=0, stdin=None, timeout=120):
    argv = [str(x) for x in argv]
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    child = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE if stdin is not None else None,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    cleanup = 'process exited'
    try:
        out, err = child.communicate(input=stdin, timeout=timeout)
    except BaseException:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.communicate()
        cleanup = 'child process group terminated'
        raise
    finally:
        with log.open('a') as stream:
            stream.write(json.dumps({'parentTaskId': os.environ.get('CLASSES_FAMILY_TASK_ID', 'assembly-arithmetic-native'),
                'cwd': str(cwd), 'command': argv, 'pid': child.pid, 'startTime': start,
                'endTime': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exitCode': child.returncode,
                'timeoutSeconds': timeout, 'childProcessGroupCleanup': cleanup}) + '\n')
    assert child.returncode != 0 if expected == 'failure' else child.returncode == expected, (argv, child.returncode, (out + err).decode(errors='replace'))
    return {'command': argv, 'exitCode': child.returncode, 'stdout': out.decode(), 'stderr': err.decode(),
                'stdinSha256': hashlib.sha256(stdin).hexdigest() if stdin is not None else None}


def signed(value):
    return value - (1 << 64) if value & SIGN else value


def oracle(op, a, b):
    if op >= 9 or (op == 3 and (b == 0 or (a == SIGN and b == MASK))):
        return (0, SENTINEL, SENTINEL, SENTINEL, SENTINEL)
    value, auxiliary, flags, defined = a, 0, 0, ALL
    if op == 0:
        value = (a + b) & MASK
        flags = (CF if a + b > MASK else 0) | (OF if not -(1 << 63) <= signed(a) + signed(b) < (1 << 63) else 0)
        temp = value
    elif op in (1, 8):
        temp = (a - b) & MASK
        flags = (CF if a < b else 0) | (OF if not -(1 << 63) <= signed(a) - signed(b) < (1 << 63) else 0)
        if op == 1:
            value = temp
    elif op == 2:
        product = signed(a) * signed(b)
        value, auxiliary, defined = product & MASK, (product >> 64) & MASK, CF | OF
        flags = defined if not -(1 << 63) <= product < (1 << 63) else 0
    elif op == 3:
        left, right = signed(a), signed(b)
        quotient = abs(left) // abs(right)
        if (left < 0) != (right < 0):
            quotient = -quotient
        value, auxiliary, defined = quotient & MASK, (left - quotient * right) & MASK, 0
    else:
        temp = (a & b) if op in (4, 7) else (a | b) if op == 5 else (a ^ b)
        if op != 7:
            value = temp
    if op not in (2, 3):
        flags |= (ZF if temp == 0 else 0) | (SF if temp & SIGN else 0)
    return (1, value, auxiliary, flags, defined)


def source_hashes():
    return {str(p.relative_to(PACK)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in PACK.rglob('*') if p.is_file()}


def gdb(binary, commands, temp, arguments=()):
    argv = ['gdb', '--batch', '--nx', '-q']
    for command in ['set pagination off', 'set disassembly-flavor intel', *commands]:
        argv += ['-ex', command]
    argv += ['--args', binary, *arguments]
    return run(argv, temp)


before = source_hashes()
version = run([args.cc, '--version'], ROOT)['stdout'].splitlines()[0]
edges = [0, 1, 2, 63, 64, 0x7fffffff, 0x80000000, SIGN - 1, SIGN, SIGN + 1, MASK - 1, MASK]
pairs = [(a, b) for a in edges for b in edges]
state = 0x6712acde12349876
for _ in range(1024):
    state = (state * 6364136223846793005 + 1442695040888963407) & MASK
    a = state
    state = (state * 6364136223846793005 + 1442695040888963407) & MASK
    pairs.append((a, state))
cases = [(op, a, b) for a, b in pairs for op in range(9)] + [(9, 0, 0), (0xffffffff, 1, 2)]
vector_input = ''.join(f'{op} {a:x} {b:x}\n' for op, a, b in cases).encode()
expected_rows = [oracle(*case) for case in cases]
profiles, rejected, regressions, traces, fault_traces = [], [], [], [], []
with tempfile.TemporaryDirectory(prefix='assembly-arithmetic-') as work:
    temp = Path(work)
    for role in ['starter', 'solution']:
        shutil.copytree(PACK / role, temp / role)
    shutil.copytree(temp / 'starter', temp / 'completed')
    learner = temp / 'completed/routine.S'
    original = learner.read_text()
    replacements = {
        '    /* TODO ARITH_MUL */\n    jmp .Lreject': '    mov r10, r8\n.global arithmetic_multiply_step\narithmetic_multiply_step:\n    imul r10',
        '    /* TODO ARITH_DIV */\n    jmp .Lreject': '    mov rdx, rax\n    sar rdx, 63\n.global arithmetic_divide_step\narithmetic_divide_step:\n    idiv r8',
    }
    for old, new in replacements.items():
        assert original.count(old) == 1
        original = original.replace(old, new)
    learner.write_text(original)
    for role in ['starter', 'solution', 'completed']:
        for profile in ['Debug', 'Release']:
            build = temp / f'{role}-{profile}'
            flag = '-O0 -g' if profile == 'Debug' else '-O2 -g -DNDEBUG'
            configure = run(['cmake', '-S', temp / role, '-B', build, '-DCMAKE_BUILD_TYPE=' + profile,
                             '-DCMAKE_C_COMPILER=' + args.cc, '-DCMAKE_ASM_COMPILER=' + args.cc,
                             '-DCMAKE_C_FLAGS_' + profile.upper() + '=' + flag,
                             '-DCMAKE_ASM_FLAGS_' + profile.upper() + '=' + flag,
                             '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'], temp)
            built = run(['cmake', '--build', build, '--verbose', '--parallel', '1'], temp)
            if role == 'starter':
                demo = run([build / 'assembly_arithmetic'], temp, expected=78)
                assert not demo['stdout'] and 'ARITH_MUL/ARITH_DIV' in demo['stderr']
                tests = run([build / 'arithmetic_contracts'], temp, expected='failure')
                rejected.append({'role': role, 'profile': profile, 'configure': configure, 'build': built, 'demo': demo, 'tests': tests})
                continue
            tests = run(['ctest', '--test-dir', build, '--output-on-failure'], temp)
            contracts = run([build / 'arithmetic_contracts'], temp)
            assert contracts['stdout'] == 'arithmetic-cases=591123\n'
            independent = run([build / 'arithmetic_contracts', '--stream'], temp, stdin=vector_input)
            observed = [tuple(int(value, 10 if i == 0 else 16) for i, value in enumerate(line.split())) for line in independent['stdout'].splitlines()]
            assert observed == expected_rows
            demos = [run([build / 'assembly_arithmetic', *extra], temp) for extra in [[], ['--changed']]]
            for demo in demos:
                lines = demo['stdout'].splitlines()
                assert len(lines) == 10
                for index, line in enumerate(lines[:9]):
                    match = re.fullmatch(r'op=(\w+) left=([0-9a-f]{16}) right=([0-9a-f]{16}) value=([0-9a-f]{16}) auxiliary=([0-9a-f]{16}) flags=([0-9a-f]{4}) defined=([0-9a-f]{4})', line)
                    assert match
                    a, b, value, auxiliary, flags, defined = [int(x, 16) for x in match.groups()[1:]]
                    assert (1, value, auxiliary, flags, defined) == oracle(index, a, b)
                a = int(re.search(r'left=([0-9a-f]+)', lines[0]).group(1), 16)
                b = int(re.search(r'right=([0-9a-f]+)', lines[0]).group(1), 16)
                assert lines[9] == f'c-mix={(((a + b) & MASK) ^ (a & b)):016x}'
            invalid = run([build / 'assembly_arithmetic', 'unexpected'], temp, expected=2)
            assert not invalid['stdout']
            faults = [run([build / 'arithmetic_fault_probe', case], temp, expected=-signal.SIGFPE) for case in ['zero', 'overflow']]
            negative = run([build / 'arithmetic_fault_probe', 'negative'], temp)
            assert negative['stdout'] == 'quotient=-5\n'
            listing = build / 'model.s'
            generated = run([args.cc, '-std=c17', *flag.split(), '-S', '-masm=intel', temp / role / 'model.c', '-o', listing], temp)
            listing_text = listing.read_text()
            assert re.search(r'^arithmetic_c_mix:', listing_text, re.MULTILINE)
            linked = run(['objdump', '-d', '-M', 'intel', '--disassemble=arithmetic_c_mix', build / 'assembly_arithmetic'], temp)
            assert '<arithmetic_c_mix>:' in linked['stdout']
            commands = json.loads((build / 'compile_commands.json').read_text())
            assert len(commands) == 7
            for item in commands:
                assert ('-O0' if profile == 'Debug' else '-O2') in item['command']
            profiles.append({'role': role, 'profile': profile, 'configure': configure, 'build': built, 'tests': tests,
                'contracts': contracts, 'contractCases': 591123, 'independent': independent,
                'independentCases': len(cases), 'demos': demos, 'invalidCommand': invalid,
                'faults': faults, 'negativeProbe': negative, 'generated': generated,
                'compilerListing': listing_text, 'linkedHelper': linked, 'compileCommands': commands})
    for role in ['solution', 'completed']:
        binary = temp / f'{role}-Debug' / 'assembly_arithmetic'
        trace = gdb(binary, ['tbreak arithmetic_add_step', 'run', 'x/i $pc', 'si',
            'printf "ADD=%016lx FLAGS=%lx\\n", $rax, $eflags & 2241',
            'tbreak arithmetic_multiply_step', 'continue', 'x/i $pc', 'si',
            'printf "MUL=%016lx:%016lx FLAGS=%lx\\n", $rdx, $rax, $eflags & 2049',
            'tbreak arithmetic_divide_step', 'continue', 'x/i $pc',
            'printf "DIVIDEND=%016lx:%016lx DIVISOR=%lx\\n", $rdx, $rax, $r8', 'si',
            'printf "DIVISION=%ld REMAINDER=%ld\\n", $rax, $rdx', 'continue'], temp)
        for token in ['ADD=8000000000000000 FLAGS=880', 'MUL=0000000000000000:8000000000000000 FLAGS=801',
                      'DIVIDEND=ffffffffffffffff:ffffffffffffffeb DIVISOR=4', 'DIVISION=-5 REMAINDER=-1', 'exited normally']:
            assert token in trace['stdout'], (token, trace)
        traces.append({'role': role, 'trace': trace, 'divisionFlagsNotAsserted': True})
        for case in ['zero', 'overflow']:
            fault_trace = gdb(temp / f'{role}-Debug' / 'arithmetic_fault_probe',
                ['tbreak arithmetic_fault_step', 'run', 'x/i $pc',
                 'printf "FAULT-INPUT=%016lx:%016lx DIVISOR=%016lx\\n", $rdx, $rax, $rsi', 'si', 'x/i $pc'], temp, [case])
            expected = '0000000000000000:0000000000000007 DIVISOR=0000000000000000' if case == 'zero' else 'ffffffffffffffff:8000000000000000 DIVISOR=ffffffffffffffff'
            assert expected in fault_trace['stdout'] and 'SIGFPE' in fault_trace['stdout'] and 'idiv' in fault_trace['stdout']
            fault_traces.append({'role': role, 'case': case, 'trace': fault_trace})
    reference = (temp / 'solution/routine.S').read_text()
    faults = {
        'unsigned-multiply': ('    imul r8', '    mul r8'),
        'incorrect-dividend': ('    cqo', '    xor edx, edx'),
        'late-flags': ('.Lcapture_all:\n    pushfq', '.Lcapture_all:\n    xor r10d, r10d\n    pushfq'),
        'preserved-register': ('.Lstore:\n', '.Lstore:\n    mov rbx, 99\n'),
    }
    for name, (old, new) in faults.items():
        assert reference.count(old) == 1
        file = temp / f'regression-{name}.S'
        file.write_text(reference.replace(old, new))
        binary = temp / f'regression-{name}'
        compiled = run([args.cc, '-std=c17', '-O0', '-g', '-I', temp / 'solution', file,
                        temp / 'solution/model.c', temp / 'solution/tests.c', temp / 'solution/abi_checks.S', '-o', binary], temp)
        failed = run([binary], temp, expected='failure')
        regressions.append({'name': name, 'compiled': compiled, 'failed': failed})
assert before == source_hashes() and not Path(work).exists()
receipt = {'event': 'verified-assembly-arithmetic-flags', 'compiler': args.cc, 'compilerVersion': version,
    'target': 'Linux x86-64 System V', 'sourceFileHashes': before, 'acceptedProfiles': profiles,
    'unfinishedProfilesRejected': rejected, 'independentVectors': cases,
    'independentVectorInputSha256': hashlib.sha256(vector_input).hexdigest(),
    'actualDebuggerTraces': traces, 'actualFaultDebuggerTraces': fault_traces,
    'controlledRegressions': regressions, 'independentLearnerCompletedOnly': 'routine.S',
    'undefinedDivisionFlagsNotAsserted': True, 'sourceFilesUnchanged': True, 'temporaryBuildCleanup': True}
args.proof.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'compiler': args.cc, 'acceptedProfiles': len(profiles),
    'contractCases': sum(p['contractCases'] for p in profiles), 'independentCases': sum(p['independentCases'] for p in profiles),
    'rejectedStarterProfiles': len(rejected), 'rejectedRegressions': len(regressions),
    'actualDebuggerTraces': len(traces), 'actualFaultDebuggerTraces': len(fault_traces), 'sourceFilesUnchanged': True, 'temporaryBuildCleanup': True}))
