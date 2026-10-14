"""Verify real function guards, ELF types, identical ASM bytes and GDB returns."""
import argparse
import datetime
import hashlib
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
PACK = ROOT / 'ASM-25-unit-12-security-and-reliability-visibility-supplemental-2'
parser = argparse.ArgumentParser()
parser.add_argument('--cc', choices=['clang', 'gcc'], required=True)
parser.add_argument('--proof', type=Path, required=True)
args = parser.parse_args()
assert platform.system() == 'Linux' and platform.machine() == 'x86_64'
args.proof.parent.mkdir(parents=True, exist_ok=True)
retained = args.proof.parent / ('hardening-observations-' + args.cc)
retained.mkdir(exist_ok=True)
process_log = args.proof.with_suffix('.processes.jsonl')


def run(command, cwd, expected=0, input_data=None, timeout=120):
    command = [str(x) for x in command]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    child = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True)
    cleanup = 'process exited'
    try:
        out, err = child.communicate(input=input_data, timeout=timeout)
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
            stream.write(json.dumps({'parentTaskId': os.environ.get('CLASSES_FAMILY_TASK_ID', 'assembly-hardening-native'),
                                         'command': command, 'cwd': str(cwd), 'pid': child.pid, 'startTime': started,
                                         'endTime': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                         'exitCode': child.returncode, 'timeoutSeconds': timeout,
                                         'childProcessGroupCleanup': cleanup}) + '\n')
    assert child.returncode != 0 if expected == 'failure' else child.returncode == expected, (command, child.returncode, (out + err).decode(errors='replace'))
    return out, err


def save(name, raw):
    (retained / name).write_bytes(raw)
    return {'filename': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def source_hashes():
    return {str(f.relative_to(PACK)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in PACK.rglob('*') if f.is_file()}


def answer(values, count):
    if not 1 <= count <= 32:
        return 0
    assert len(values) == count
    return (5381 * 33 ** count + sum(x * 33 ** (count - i - 1) for i, x in enumerate(values))) % (1 << 64)


cases = [(0, []), (-1, []), (-(1 << 63), []), (33, []), ((1 << 63) - 1, []),
         (1, [0]), (1, [255]), (32, list(range(32))), (32, [255] * 32), (8, list(b'Assembly'))]
state = 0x9137abc72935de64
for _ in range(10000):
    state = (state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
    count = state % 33
    values = []
    for _ in range(count):
        state = (state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        values.append(state >> 56)
    cases.append((count, values))
assert len(cases) == 10010
oracle = ''.join(' '.join(map(str, [count, answer(values, count), *values])) + '\n' for count, values in cases).encode()
before = source_hashes()
assert len(before) == 19
for file in ('hardening.h', 'model.c', 'bytes.S', 'main.c', 'tests.c', 'abi_checks.S', 'CMakeLists.txt'):
    assert (PACK / 'starter' / file).read_bytes() == (PACK / 'solution' / file).read_bytes()
for role in ('starter', 'solution'):
    for worksheet in ('analysis.md', 'trace.md'):
        text = (PACK / role / worksheet).read_text()
        assert ('TODO ' in text) == (role == 'starter')
version = run([args.cc, '--version'], ROOT)[0].decode().splitlines()[0]
profiles, regressions, traces = [], [], []
asm_hash = None
with tempfile.TemporaryDirectory(prefix='assembly-hardening-') as work:
    temp = Path(work)
    for role in ('starter', 'solution'):
        shutil.copytree(PACK / role, temp / role)
        for mode in ('Debug', 'Release'):
            for feature in ('baseline', 'guard', 'guard-pie'):
                key = role + '-' + mode + '-' + feature
                build = temp / key
                flag = '-DCMAKE_C_FLAGS_DEBUG=-O0 -g' if mode == 'Debug' else '-DCMAKE_C_FLAGS_RELEASE=-O2 -g -DNDEBUG'
                run(['cmake', '-S', temp / role, '-B', build, '-DCMAKE_BUILD_TYPE=' + mode,
                     '-DCMAKE_C_COMPILER=' + args.cc, '-DCMAKE_ASM_COMPILER=' + args.cc,
                     '-DLAB_PROFILE=' + feature, flag], temp)
                run(['cmake', '--build', build, '--parallel', '1'], temp)
                run(['ctest', '--test-dir', build, '--output-on-failure'], temp)
                executable = build / 'assembly_hardening'
                contracts = build / 'hardening_contracts'
                physical, err = run([contracts], temp)
                assert physical == b'hardening physical and fixed cases passed: 69\n' and not err
                independent, err = run([contracts, '--oracle'], temp, input_data=oracle)
                assert independent == b'hardening oracle cases passed: 10010\n' and not err
                for values in (None, 'ABC', '', 'Z' * 32, '\u00b5'):
                    text = 'Assembly' if values is None else values
                    raw, err = run([executable] + ([] if values is None else [values]), temp)
                    data = text.encode()
                    value = answer(list(data), len(data))
                    assert raw == f'count={len(data)} c={value} asm={value} match=yes\n'.encode() and not err
                for invalid in (['Z' * 33], ['A', 'B']):
                    raw, err = run([executable, *invalid], temp, expected=2)
                    assert not raw and b'usage:' in err
                binary = executable.read_bytes()
                elf_type = int.from_bytes(binary[16:18], 'little')
                assert binary[:6] == b'\x7fELF\x02\x01' and int.from_bytes(binary[18:20], 'little') == 62
                assert elf_type == (3 if feature == 'guard-pie' else 2)
                header, _ = run(['readelf', '-h', executable], temp)
                c, _ = run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--disassemble=checksum_c', executable], temp)
                assembly, _ = run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--disassemble=checksum_asm', executable], temp)
                assert b'<checksum_c>:' in c and b'<checksum_asm>:' in assembly
                protected = feature != 'baseline'
                assert (b'__stack_chk_fail' in c) == protected
                assert (b'fs:0x28' in c) == protected
                assert b'__stack_chk_fail' not in assembly and b'fs:' not in assembly
                assert b'movzx' in assembly and b'imul' in assembly
                text_file = retained / (key + '-asm-text.bin')
                run(['objcopy', '--dump-section', '.text=' + str(text_file), build / 'CMakeFiles/checksums.dir/bytes.S.o'], temp)
                raw_asm = text_file.read_bytes()
                assert raw_asm
                digest = hashlib.sha256(raw_asm).hexdigest()
                if asm_hash is None:
                    asm_hash = digest
                assert digest == asm_hash
                evidence = {'header': save(key + '-elf.txt', header), 'c': save(key + '-c.txt', c),
                                'assembly': save(key + '-asm.txt', assembly), 'machineCode': save(key + '-asm-text.bin', raw_asm)}
                profiles.append({'role': role, 'optimization': mode, 'feature': feature, 'elfType': elf_type,
                                     'cGuardObserved': protected, 'assemblyGuardObserved': False,
                                     'handwrittenBytesUnchanged': True, 'physicalCases': 69, 'oracleCases': 10010,
                                     'nativeCases': 10079, 'preservedRegisters': 6, 'workingBaseline': True,
                                     'worksheetCompletionNotInferred': True, 'evidence': evidence})
    original = (temp / 'starter/bytes.S').read_text()
    mutations = [('skipped-first-byte', '    xor ecx, ecx', '    mov ecx, 1'),
                 ('one-past-count', '    jge .Lchecksum_done', '    jg .Lchecksum_done'),
                 ('wrong-read-width', '    movzx edx, BYTE PTR [rdi+rcx]', '    mov edx, DWORD PTR [rdi+rcx]'),
                 ('truncated-result', '.Lchecksum_done:\n    ret', '.Lchecksum_done:\n    mov eax, eax\n    ret'),
                 ('preserved-register', '.Lchecksum_done:\n    ret', '.Lchecksum_done:\n    mov rbx, 1\n    ret'),
                 ('invalid-count-result', '    xor eax, eax', '    mov eax, 5381')]
    for name, old, new in mutations:
        assert original.count(old) == 1
        folder = temp / name
        shutil.copytree(temp / 'starter', folder)
        (folder / 'bytes.S').write_text(original.replace(old, new))
        executable = folder / 'contracts'
        run([args.cc, '-std=c17', '-Wall', '-Wextra', '-Wpedantic', '-Wconversion', '-Werror',
             'tests.c', 'model.c', 'abi_checks.S', 'bytes.S', '-o', executable], folder)
        run([executable], folder, expected='failure')
        regressions.append({'name': name, 'rejected': True})
    folder = temp / 'c-result-width'
    shutil.copytree(temp / 'starter', folder)
    file = folder / 'model.c'
    old = 'value = value * UINT64_C(33) + scratch[i];'
    assert file.read_text().count(old) == 1
    file.write_text(file.read_text().replace(old, 'value = (uint32_t)(value * UINT64_C(33) + scratch[i]);'))
    run([args.cc, '-std=c17', '-Wall', '-Wextra', '-Wpedantic', '-Wconversion', '-Werror',
         'tests.c', 'model.c', 'abi_checks.S', 'bytes.S', '-o', folder / 'contracts'], folder)
    run([folder / 'contracts'], folder, expected='failure')
    regressions.append({'name': 'c-result-width', 'rejected': True})
    value = answer(list(b'Assembly'), 8)
    for feature in ('baseline', 'guard-pie'):
        executable = temp / ('starter-Debug-' + feature) / 'assembly_hardening'
        script = temp / (feature + '.gdb')
        script.write_text('set pagination off\nset confirm off\nset disassembly-flavor intel\nset disable-randomization off\ntbreak *checksum_c\nrun\nprintf "LAB_C_COUNT=%ld\\n", $rsi\nx/i $pc\ndisassemble checksum_c\nsi\nfinish\nprintf "LAB_C_RETURN=%llu\\n", $rax\ntbreak *checksum_asm\ncontinue\nprintf "LAB_ASM_COUNT=%ld\\n", $rsi\nx/i $pc\ndisassemble checksum_asm\nsi\nfinish\nprintf "LAB_ASM_RETURN=%llu\\n", $rax\ncontinue\n')
        raw, err = run(['gdb', '--batch', '-x', script, executable], temp)
        assert b'LAB_C_COUNT=8' in raw and b'LAB_ASM_COUNT=8' in raw
        assert f'LAB_C_RETURN={value}'.encode() in raw
        assert f'LAB_ASM_RETURN={value}'.encode() in raw
        assert b'exited normally' in raw
        assert (b'__stack_chk_fail' in raw) == (feature == 'guard-pie')
        assert len(re.findall(rb'=> 0x[0-9a-f]+', raw)) >= 2
        traces.append({'feature': feature, 'bothEntriesObserved': True, 'bothReturnsObserved': True,
                           'defaultCount': 8, 'checksum': value, 'raw': save(feature + '-trace.txt', raw + err),
                           'randomizationSetting': 'off: inferior randomization left enabled',
                           'repeatedAddressesRequired': False, 'canaryFailureExecuted': False})
assert source_hashes() == before
record = {'compiler': args.cc, 'version': version, 'sourceHashes': before, 'profiles': profiles,
              'profileCount': 12, 'nativeCases': 120948, 'regressions': regressions, 'traces': traces,
              'assemblyMachineCodeSha256': asm_hash, 'sourceUnchanged': True,
              'allThreeProfilesObserved': True, 'realGdb': True, 'rawObservationDirectory': retained.name}
args.proof.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'event': 'verified-assembly-hardening-native', 'compiler': args.cc,
                      'profiles': 12, 'nativeCases': 120948, 'regressions': 7, 'rawTraces': 2}), flush=True)
