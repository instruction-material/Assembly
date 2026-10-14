"""Verify equivalent loops, actual timing CSV and physical native contracts."""
import argparse
import csv
import datetime
import hashlib
import io
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'ASM-10-unit-11-performance-and-code-shape'
MASK = (1 << 64) - 1
PATTERNS = ['nonnegative', 'alternating', 'seeded-mixed']
VARIANTS = ['branch-sequential', 'cmov-sequential', 'indexed-identity', 'indexed-permuted']
parser = argparse.ArgumentParser()
parser.add_argument('--cc', choices=['clang', 'gcc'], required=True)
parser.add_argument('--skip-debugger', action='store_true')
parser.add_argument('--proof', type=Path, required=True)
args = parser.parse_args()
assert platform.system() == 'Linux' and platform.machine() == 'x86_64'
args.proof.parent.mkdir(parents=True, exist_ok=True)
process_log = args.proof.with_suffix('.processes.jsonl')
retained = args.proof.parent / ('performance-' + args.cc + '-observations')
retained.mkdir(exist_ok=True)

def run(command, cwd, expected=0, input_data=None, timeout=120):
    command = [str(x) for x in command]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    child = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    cleanup = 'process exited'
    try:
        (out, err) = child.communicate(input=input_data, timeout=timeout)
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
        with process_log.open('a') as stream:
            stream.write(json.dumps({'parentTaskId': os.environ.get('CLASSES_FAMILY_TASK_ID', 'assembly-performance-native'), 'command': command, 'cwd': str(cwd), 'pid': child.pid, 'startTime': started, 'endTime': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exitCode': child.returncode, 'timeoutSeconds': timeout, 'childProcessGroupCleanup': cleanup}) + '\n')
    assert child.returncode != 0 if expected == 'failure' else child.returncode == expected, (command, child.returncode, (out + err).decode(errors='replace'))
    return (out, err)

def signed(bits):
    return bits - (1 << 64) if bits >= 1 << 63 else bits

def next_state(state):
    return state * 6364136223846793005 + 1442695040888963407 & MASK

def dataset(count, pattern):
    state = 9317844757679152146 + pattern
    values = []
    for index in range(count):
        state = next_state(state)
        magnitude = state & (1 << 63) - 1
        values.append(magnitude if pattern == 0 else (magnitude if index % 2 == 0 else -magnitude - 1) if pattern == 1 else signed(state))
    permutation = list(range(count))
    for remaining in range(count, 1, -1):
        state = next_state(state)
        chosen = state % remaining
        (permutation[remaining - 1], permutation[chosen]) = (permutation[chosen], permutation[remaining - 1])
    assert sorted(permutation) == list(range(count))
    return (values, permutation)

def validate_csv(text, count, repeats, trials):
    reader = csv.DictReader(io.StringIO(text))
    assert reader.fieldnames == ['pattern', 'variant', 'trial', 'count', 'repeats', 'elapsed_ns', 'checksum', 'expected_checksum', 'seed']
    rows = list(reader)
    assert len(rows) == 3 * 4 * trials
    expected_order = [(PATTERNS[p], VARIANTS[(trial + offset) % 4], trial) for p in range(3) for trial in range(trials) for offset in range(4)]
    assert [(row['pattern'], row['variant'], int(row['trial'])) for row in rows] == expected_order
    for row in rows:
        pattern = PATTERNS.index(row['pattern'])
        (values, permutation) = dataset(count, pattern)
        total = sum(x for x in values if x >= 0) & MASK
        assert sum(values[i] for i in permutation if values[i] >= 0) & MASK == total
        checksum = total * repeats & MASK
        assert int(row['count']) == count and int(row['repeats']) == repeats
        assert int(row['seed']) == 9317844757679152146 + pattern
        assert int(row['checksum']) == int(row['expected_checksum']) == checksum
        assert re.fullmatch('[0-9]+', row['elapsed_ns'])
    return rows

def source_hashes():
    return {str(f.relative_to(PACK)): hashlib.sha256(f.read_bytes()).hexdigest() for f in PACK.rglob('*') if f.is_file()}
fixed = [[], [-3, 0, 5, (1 << 63) - 1, (1 << 63) - 1], [-(1 << 63)], [(1 << 63) - 1], [0], [-1], [1], [-(1 << 63), (1 << 63) - 1, 0, 1], [1 << 32, (1 << 32) + 7, -1], [-(1 << 32), 1 << 40, -7], [(1 << 63) - 1] * 3, [5, -3, 7, -1]]
cases = [(len(values), values, list(reversed(range(len(values))))) for values in fixed]
state = 11830244935645629377
for _ in range(10000):
    state = next_state(state)
    count = state % 65
    (values, indices) = ([], [])
    for _ in range(count):
        state = next_state(state)
        values.append(signed(state))
    for _ in range(count):
        state = next_state(state)
        indices.append(state % count)
    cases.append((count, values, indices))
cases.extend((count, [], []) for count in [-1, -2, -(1 << 63)])
assert len(cases) == 10015
oracle_input = ''.join(' '.join(map(str, [count, *values, *indices, sum(x for x in values if x >= 0) & MASK, sum(values[i] for i in indices if values[i] >= 0) & MASK])) + '\n' for (count, values, indices) in cases).encode()
before = source_hashes()
assert len(before) == 17
assert all('TODO ' + key in (PACK / 'starter/analysis.md').read_text() for key in ['TARGET', 'PREDICT', 'CORRECT', 'MEASURE', 'MAP', 'CASE', 'EXPLAIN'])
assert 'TODO' not in (PACK / 'solution/analysis.md').read_text()
for name in ['loops.S', 'performance.h', 'dataset.c', 'main.c', 'tests.c', 'abi_checks.S', 'CMakeLists.txt']:
    assert (PACK / 'starter' / name).read_bytes() == (PACK / 'solution' / name).read_bytes()
version = run([args.cc, '--version'], ROOT)[0].decode().splitlines()[0]
(profiles, regressions, observations) = ([], [], [])
with tempfile.TemporaryDirectory(prefix='assembly-performance-') as work:
    temp = Path(work)
    for role in ['starter', 'solution']:
        shutil.copytree(PACK / role, temp / role)
        for (profile, optimization) in [('Debug', '-O0'), ('Release', '-O2')]:
            build = temp / (role + '-' + profile)
            flag = '-DCMAKE_C_FLAGS_DEBUG=-O0 -g' if profile == 'Debug' else '-DCMAKE_C_FLAGS_RELEASE=-O2 -g -DNDEBUG'
            run(['cmake', '-S', temp / role, '-B', build, '-DCMAKE_BUILD_TYPE=' + profile, '-DCMAKE_C_COMPILER=' + args.cc, '-DCMAKE_ASM_COMPILER=' + args.cc, flag], temp)
            run(['cmake', '--build', build, '--parallel', '1'], temp)
            run(['ctest', '--test-dir', build, '--output-on-failure'], temp)
            executable = build / 'assembly_performance'
            (demo, err) = run([executable, '--example'], temp)
            assert demo == b'branch=3 cmov=3 indexed=3 expected=3\n' and (not err)
            (physical, err) = run([build / 'performance_contracts'], temp)
            assert physical == b'performance physical and fixed cases passed: 11\n' and (not err)
            (oracle, err) = run([build / 'performance_contracts', '--oracle'], temp, input_data=oracle_input)
            assert oracle == b'performance oracle cases passed: 10015\n' and (not err)
            for (suffix, count, repeats, trials) in [('default', 4096, 32, 5), ('changed', 64, 3, 2)]:
                command = [executable, '--benchmark'] + ([] if suffix == 'default' else [str(count), str(repeats), str(trials)])
                (raw, err) = run(command, temp)
                assert not err
                rows = validate_csv(raw.decode(), count, repeats, trials)
                filename = role + '-' + profile + '-' + suffix + '.csv'
                (retained / filename).write_bytes(raw)
                observations.append({'role': role, 'profile': profile, 'fixture': suffix, 'rows': len(rows), 'count': count, 'repeats': repeats, 'trials': trials, 'filename': filename, 'sha256': hashlib.sha256(raw).hexdigest(), 'realElapsedValues': True, 'checksumOracleAccepted': True, 'rotatedOrder': True, 'speedThresholdApplied': False})
            for arguments in [['--benchmark', '63', '1', '1'], ['--benchmark', '128', '0', '1'], ['--benchmark', '128', '1', '22'], ['--benchmark', '1048576', '1024', '21'], ['--benchmark', '-64', '1', '1'], ['--benchmark', '64', '1'], ['--example', 'extra']]:
                (out, error) = run([executable, *arguments], temp, expected=2)
                assert not out and b'usage:' in error
            listings = {}
            for function in ['sum_nonnegative_branch', 'sum_nonnegative_cmov', 'sum_nonnegative_indexed']:
                (raw, _) = run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--disassemble=' + function, executable], temp)
                assert ('<' + function + '>:').encode() in raw
                assert re.search(b'\\bret\\b', raw)
                if function.endswith('cmov'):
                    assert b'cmovns' in raw
                filename = role + '-' + profile + '-' + function + '.txt'
                (retained / filename).write_bytes(raw)
                listings[function] = {'filename': filename, 'sha256': hashlib.sha256(raw).hexdigest()}
            profiles.append({'role': role, 'profile': profile, 'optimization': optimization, 'performanceCases': 10026, 'independentPythonOracleCases': 10015, 'physicalAndFixedCases': 11, 'preservedRegisters': 6, 'workingBaseline': True, 'worksheetCompletionNotInferred': True, 'actualTimingRows': 84, 'disassembly': listings})
    mutations = [('unsigned-eligibility', '    jns .Lbranch_add', '    jae .Lbranch_add'), ('conditional-move-width', '    cmovns r9, r8', '    cmovns r9d, r8d'), ('data-stride', '[rdi+r8*8]', '[rdi+r8*4]'), ('skipped-first', '    xor ecx, ecx\n.Lbranch_loop:', '    mov ecx, 1\n.Lbranch_loop:'), ('ignored-index-order', '    mov r8, QWORD PTR [rsi+rcx*8]', '    mov r8, rcx'), ('result-width', '.Lcmov_done:\n    ret', '.Lcmov_done:\n    mov eax, eax\n    ret'), ('preserved-register', '.Lbranch_done:\n    ret', '.Lbranch_done:\n    mov r12, 42\n    ret'), ('negative-count-read', '    jle .Lindexed_done', '    je .Lindexed_done')]
    original = (PACK / 'starter/loops.S').read_text()
    for (name, old, new) in mutations:
        assert original.count(old) == 1
        mutant = temp / ('mutant-' + name)
        shutil.copytree(temp / 'starter', mutant)
        (mutant / 'loops.S').write_text(original.replace(old, new))
        executable = mutant / 'contracts'
        run([args.cc, '-std=c17', '-Wall', '-Wextra', '-Wpedantic', '-Wconversion', '-Werror', 'tests.c', 'abi_checks.S', 'loops.S', '-o', executable], mutant)
        run([executable], mutant, expected='failure')
        regressions.append({'name': name, 'compiled': True, 'rejectedByUnchangedContracts': True})
    if args.skip_debugger:
        debugger = {'status': 'skipped'}
    else:
        executable = temp / 'starter-Debug/assembly_performance'
        (raw, err) = run(['gdb', '--batch', '--nx', '-q', executable, '-ex', 'set disassembly-flavor intel', '-ex', 'tbreak *performance_branch_decision', '-ex', 'run --example', '-ex', 'printf "PERF-before count=%lld index=%lld value=%lld\\n", $rsi, $rcx, $r8', '-ex', 'printf "PERF-flags SF=%d OF=%d ZF=%d CF=%d\\n", (int)(($eflags>>7)&1), (int)(($eflags>>11)&1), (int)(($eflags>>6)&1), (int)($eflags&1)', '-ex', 'si', '-ex', 'printf "PERF-after-branch\\n"', '-ex', 'x/i $pc', '-ex', 'printf "PERF-next-matches=%d\\n", (void *)$pc == (void *)&performance_branch_advance', '-ex', 'si', '-ex', 'printf "PERF-after-index=%lld\\n", $rcx', '-ex', 'finish', '-ex', 'printf "PERF-result=%llu\\n", $rax', '-ex', 'continue'], temp)
        trace = raw + err
        assert b'PERF-before count=5 index=0 value=-3' in trace
        assert b'PERF-flags SF=1 OF=0 ZF=0 CF=0' in trace
        assert b'PERF-next-matches=1' in trace and b'PERF-after-index=1' in trace
        assert b'PERF-result=3' in trace
        after = trace.split(b'PERF-after-branch\n', 1)[1].split(b'\n', 1)[0]
        assert re.search(b'inc\\s+rcx', after)
        (retained / 'gdb-branch.txt').write_bytes(trace)
        (clock, err) = run(['gdb', '--batch', '--nx', '-q', executable, '-ex', 'tbreak clock_gettime', '-ex', 'run --benchmark 64 1 1', '-ex', 'printf "PERF-clock-id=%d\\n", (int)$rdi', '-ex', 'continue'], temp)
        clock_trace = clock + err
        assert b'PERF-clock-id=1' in clock_trace
        assert b'pattern,variant,trial,count,repeats,elapsed_ns' in clock_trace
        (retained / 'gdb-clock.txt').write_bytes(clock_trace)
        debugger = {'status': 'accepted', 'signedDecisionAndReturn': True, 'actualMonotonicClockCall': True, 'branchTrace': trace.decode(), 'clockTrace': clock_trace.decode()}
assert not Path(work).exists() and before == source_hashes()
receipt = {'event': 'verified-assembly-performance', 'compiler': args.cc, 'compilerVersion': version, 'acceptedProfiles': profiles, 'controlledRegressions': regressions, 'independentOracle': 'Python full signed integers, bounded index enumeration and modulo sums', 'observations': observations, 'debugger': debugger, 'workingRolePrograms': True, 'requiredLearnerArtifact': 'analysis.md', 'worksheetCompletionNotInferred': True, 'noUniversalWinner': True, 'speedThresholdApplied': False, 'sourceFilesUnchanged': True, 'temporaryBuildCleanup': True}
args.proof.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'event': receipt['event'], 'compiler': args.cc, 'performanceCases': sum(x['performanceCases'] for x in profiles), 'acceptedProfiles': len(profiles), 'regressionsRejected': len(regressions), 'actualTimingRows': sum(x['rows'] for x in observations), 'debugger': debugger['status']}))
