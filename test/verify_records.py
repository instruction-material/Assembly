"""Verify real record loads, guards and GDB traces on Linux x86-64."""
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
PACK = ROOT / 'ASM-05-unit-1-machine-model-and-toolchain'
parser = argparse.ArgumentParser()
parser.add_argument('--cc', choices=['clang', 'gcc'], required=True)
parser.add_argument('--proof', type=Path, required=True)
args = parser.parse_args()
assert platform.system() == 'Linux' and platform.machine() == 'x86_64'
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
args.proof.parent.mkdir(parents=True, exist_ok=True)
log = args.proof.with_suffix('.processes.jsonl')


def run(argv, cwd, expected=0, timeout=120):
    argv = [str(x) for x in argv]
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    child = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=True)
    cleanup = 'process exited'
    try:
        out, err = child.communicate(timeout=timeout)
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
            stream.write(json.dumps({'parentTaskId': os.environ.get('CLASSES_FAMILY_TASK_ID', 'assembly-record-model-native'),
                'cwd': str(cwd), 'command': argv, 'pid': child.pid, 'startTime': start,
                'endTime': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'exitCode': child.returncode, 'timeoutSeconds': timeout,
                'childProcessGroupCleanup': cleanup}) + '\n')
    assert (child.returncode != 0 if expected == 'failure' else child.returncode == expected), (argv, child.returncode, (out+err).decode(errors='replace'))
    return {'command': argv, 'exitCode': child.returncode, 'stdout': out.decode(errors='replace'), 'stderr': err.decode(errors='replace')}


def source_hashes():
    return {str(f.relative_to(PACK)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in PACK.rglob('*') if f.is_file()}


def rows(text, changed):
    parsed = [tuple(int(value, 16 if i == 1 else 10) for i, value in enumerate(match))
              for match in re.findall(r'^record=(\d+) address=0x([0-9a-f]+) delta=(-?\d+) size=(\d+) tag=(\d+)$', text, re.MULTILINE)]
    expected = [(32767,32768,1),(-32768,65535,4294967295),(0,1,2147483648),(-2,0,16909060)] if changed else [(-32768,65535,2147483648),(-1,0,4294967295),(32767,1,305419896),(1,32768,0)]
    assert len(parsed) == 4 and len(text.splitlines()) == 4
    for index, record in enumerate(parsed):
        assert record[0] == index and record[1] == parsed[0][1] + index * 8
        assert record[2:] == expected[index]
    return parsed


before = source_hashes()
version = run([args.cc, '--version'], ROOT)['stdout'].splitlines()[0]
profiles, rejected, regressions, traces = [], [], [], []
with tempfile.TemporaryDirectory(prefix='assembly-records-') as work:
    temp = Path(work)
    for role in ['starter', 'solution']:
        shutil.copytree(PACK / role, temp / role)
    shutil.copytree(temp / 'starter', temp / 'completed')
    code = temp / 'completed/routine.S'
    original = code.read_text()
    first = original.index('    /* TODO RECORD_DECODE:')
    last = original.index('.size decode_record,')
    reference = (temp / 'solution/routine.S').read_text()
    replacement = reference[reference.index('    xor eax, eax'):reference.index('.size decode_record,')]
    code.write_text(original[:first] + replacement + original[last:])
    for f in (temp / 'starter').iterdir():
        if f.name != 'routine.S':
            assert f.read_bytes() == (temp / 'completed' / f.name).read_bytes()
    for role in ['starter', 'solution', 'completed']:
        for profile in ['Debug', 'Release']:
            build = temp / (role + '-' + profile)
            run(['cmake','-S',temp/role,'-B',build,'-DCMAKE_BUILD_TYPE='+profile,
                 '-DCMAKE_C_COMPILER='+args.cc,'-DCMAKE_ASM_COMPILER='+args.cc], temp)
            run(['cmake','--build',build,'--parallel','1'], temp)
            ctest = run(['ctest','--test-dir',build,'--output-on-failure'], temp, expected='failure' if role == 'starter' else 0)
            contracts = run([build/'assembly_contracts'], temp, expected=1 if role == 'starter' else 0)
            demo = run([build/'assembly_demo'], temp, expected=78 if role == 'starter' else 0)
            if role == 'starter':
                assert 'decode failed index=0 raw=0' in contracts['stderr']
                assert not demo['stdout'] and 'unfinished or incorrect' in demo['stderr']
                rejected.append({'role': role,'profile': profile,'contracts': contracts,'demo': demo,'ctest': ctest})
                continue
            assert contracts['stdout'] == 'record cases=196609 guard=1 abi=6 rejected=5\n' and not contracts['stderr']
            changed = run([build/'assembly_demo','--changed'], temp)
            usage = run([build/'assembly_demo','--unknown'], temp, expected=64)
            assert not usage['stdout'] and 'usage:' in usage['stderr']
            profiles.append({'role': role,'profile': profile,'contractCases': 196609,'contracts': contracts,
                                 'defaultRows': rows(demo['stdout'],False),'changedRows': rows(changed['stdout'],True),
                                 'demo': demo,'changed': changed,'usage': usage,'ctest': ctest})
    for name, old, new in [
        ('wrong-sign-extension','movsx r9, word ptr [r8]','movzx r9, word ptr [r8]'),
        ('wrong-tag-extension','mov r9d, dword ptr [r8 + 4]','movsxd r9, dword ptr [r8 + 4]'),
        ('wrong-stride','[rdi + rdx*8]','[rdi + rdx*4]'),
        ('off-by-one-guard','jae .Ldone','ja .Ldone'),
    ]:
        folder = temp / name
        shutil.copytree(temp/'solution', folder)
        path = folder/'routine.S'
        text = path.read_text()
        assert text.count(old) == 1
        path.write_text(text.replace(old,new))
        run([args.cc,'-std=c17','-Wall','-Wextra','-Wpedantic','-Wconversion','-Werror',
             'tests.c','abi_checks.S','routine.S','-o','broken'], folder)
        result = run([folder/'broken'], folder, expected='failure')
        regressions.append({'kind': name,'result': result,'rejected': True})
    for role in ['solution','completed']:
        binary = temp/(role+'-Debug')/'assembly_demo'
        disassembly = run(['objdump','-d','-M','intel',binary], temp)
        assert '<decode_record>:' in disassembly['stdout'] and 'movsx' in disassembly['stdout'] and 'movzx' in disassembly['stdout']
        commands = ['set disassembly-flavor intel','tbreak record_signed_load',
                    'tbreak record_unsigned_load','tbreak record_tag_load','run',
                    'set $dst = (unsigned char*)$rcx',
                    'printf "ADDRESS-MATCH=%d\\n", $r8 == $rdi + $rdx*8',
                    'x/8bx $r8','stepi','printf "SIGNED=%ld\\n", $r9',
                    'continue','stepi','printf "UNSIGNED=%lu\\n", $r9',
                    'continue','stepi','printf "TAG=%lu\\n", $r9','finish',
                    'printf "RETURN=%lu\\n", $rax',
                    'printf "FIELDS=%ld,%lu,%lu\\n", *(long*)($dst+8), *(unsigned long*)($dst+16), *(unsigned long*)($dst+24)',
                    'continue']
        argv = ['gdb','--batch','--nx','-q',binary]
        for command in commands:
            argv += ['-ex',command]
        trace = run(argv, temp)
        for expected in ['ADDRESS-MATCH=1','SIGNED=-32768','UNSIGNED=65535','TAG=2147483648',
                         'RETURN=1','FIELDS=-32768,65535,2147483648','exited normally']:
            assert expected in trace['stdout'], (expected,trace)
        traces.append({'role': role,'trace': trace,'disassembly': disassembly})
assert not Path(work).exists() and before == source_hashes()
receipt = {'event': 'verified-assembly-record-model', 'compiler': args.cc,'compilerVersion': version,
               'target': 'Linux x86-64 System V','sourceFileHashes': before,
               'acceptedProfiles': profiles,'unfinishedProfilesRejected': rejected,
               'controlledRegressions': regressions,'debuggerTraces': traces,
               'independentLearnerCompletedOnly': 'routine.S','sourceFilesUnchanged': True,
               'temporaryBuildCleanup': True}
args.proof.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'event': receipt['event'],'compiler': args.cc,'acceptedProfiles': len(profiles),
                      'contractCases': sum(x['contractCases'] for x in profiles),
                      'unfinishedProfilesRejected': len(rejected),'controlledRegressionsRejected': len(regressions),
                      'actualDebuggerTraces': len(traces),'sourceFilesUnchanged': True,'temporaryBuildCleanup': True}))
