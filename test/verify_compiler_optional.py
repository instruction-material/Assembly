"""Execute byte-promotion and valid-alias compiler observations on Linux x86-64."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import time

PACKS = {'promotions': 'ASM-19-unit-9-reading-compiler-output-supplemental-2',
         'aliasing': 'ASM-20-unit-9-reading-compiler-output-supplemental-3'}
ROLE_FILES = ('baseline.c', 'operation.c', 'main.c', 'lab.h', 'model.c', 'tests.c', 'abi_checks.S', 'CMakeLists.txt', 'analysis.md')
MASK = (1 << 64) - 1
FIXED = (0, 1, 2, 31, 32, 63, 64, 65, 127, 128, 255, (1 << 63) - 1, 1 << 63, (1 << 63) + 1, 0xaaaaaaaaaaaaaaaa, MASK)


def model(mode, initial, incoming):
    if mode == 'promotions':
        index = initial & 7
        raw = (incoming >> (8 * index)) & 255
        signed = raw if raw < 128 else raw - 256
        threshold = ((initial >> 8) & 255) - 128
        return [index, signed & MASK, raw, int(signed < threshold), int(raw < threshold)]
    slots = [initial, incoming]
    right = 0 if initial & 1 else 1
    slots[0] = (slots[0] + incoming) & MASK
    slots[right] ^= slots[0]
    separate_left = (initial + incoming) & MASK
    return [slots[0], slots[0], slots[1], separate_left, incoming ^ separate_left]


def cases(mode):
    result = [(left, right) for left in FIXED for right in FIXED]
    state = 0xdecafbad87912345
    for _ in range(10013):
        state = (state * 6364136223846793005 + 1442695040888963407) & MASK
        left = state
        state = (state * 6364136223846793005 + 1442695040888963407) & MASK
        result.append((left, state))
    if mode == 'promotions':
        result.extend((index | (128 << 8), byte << (index * 8)) for index in range(8) for byte in range(256))
    return result


def demo_inputs(mode, changed=False):
    return ((0, 0) if changed else (0x8007, 0x80ff7f0100fe0281)) if mode == 'promotions' else ((2, 5) if changed else (3, 5))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc', choices=('clang', 'gcc'), required=True)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--source-only', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    ast.parse(Path(__file__).read_text(), feature_version=(3, 10))
    sources = {}
    for pack in PACKS.values():
        assert [name for name in ROLE_FILES if (root / pack / 'starter' / name).read_bytes() != (root / pack / 'solution' / name).read_bytes()] == ['analysis.md']
        for name in ['README.md'] + [role + '/' + name for role in ('starter', 'solution') for name in ROLE_FILES]:
            body = (root / pack / name).read_bytes()
            assert body
            sources[pack + '/' + name] = hashlib.sha256(body).hexdigest()
        assert all('TODO ' + name in (root / pack / 'starter/analysis.md').read_text() for name in ('TARGET', 'PREDICT', 'TYPES', 'MAP', 'OPTIMIZE', 'TRACE', 'REGRESSION'))
        assert 'TODO' not in (root / pack / 'solution/analysis.md').read_text()
    assert len(sources) == 38
    proof = dict(compiler=args.cc, sourceFiles=sources, profiles=[], debuggerTraces=[], nativeExecuted=False)
    args.proof = args.proof.resolve()
    args.proof.parent.mkdir(parents=True, exist_ok=True)
    if args.source_only:
        args.proof.write_text(json.dumps(proof, indent=2) + '\n')
        print('38 source files and Python 3.10 syntax accepted; native execution still required')
        return
    assert platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64')
    assert os.geteuid() != 0
    cc = shutil.which(args.cc)
    assert cc and all(shutil.which(tool) for tool in ('cmake', 'ctest', 'objdump', 'readelf', 'gdb'))
    work = args.proof.parent / ('compiler-optional-' + args.cc + '-observations')
    work.mkdir(exist_ok=False)
    process_log = args.proof.with_suffix('.processes.jsonl')

    def run(argv, cwd, label, stdin=None, expected=0, timeout=120):
        argv = list(map(str, argv))
        child = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        entry = dict(parentTask='assembly-compiler-optional-native', parentPid=os.getpid(), pid=child.pid, command=argv,
                     cwd=str(cwd), startTime=time.time(), timeoutSeconds=timeout)
        if stdin is not None:
            entry.update(stdinSha256=hashlib.sha256(stdin).hexdigest(), stdinBytes=len(stdin))
            (cwd / (label + '.stdin.txt')).write_bytes(stdin)
        with process_log.open('a') as stream:
            stream.write(json.dumps(dict(entry, event='start')) + '\n')
        cleanup = 'process exited'
        try:
            out, err = child.communicate(input=stdin, timeout=timeout)
        except BaseException:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                out, err = child.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                out, err = child.communicate()
            cleanup = 'owned process group terminated and reaped'
            raise
        finally:
            with process_log.open('a') as stream:
                stream.write(json.dumps(dict(entry, event='end', endTime=time.time(), exitCode=child.returncode,
                                             childProcessGroupCleanup=cleanup)) + '\n')
        (cwd / (label + '.stdout.txt')).write_bytes(out)
        (cwd / (label + '.stderr.txt')).write_bytes(err)
        assert child.returncode == expected if expected is not None else child.returncode != 0, (label, child.returncode, err.decode(errors='replace'))
        return out, err

    proof['compilerVersion'] = run([cc, '--version'], work, 'compiler-version')[0].decode()
    for mode, pack in PACKS.items():
        inputs = cases(mode)
        payload = ''.join(f'{left:016x} {right:016x}\n' for left, right in inputs).encode()
        expected_rows = [model(mode, left, right) for left, right in inputs]
        for role, kind in [(role, kind) for role in ('starter', 'solution') for kind in ('O0', 'O2')] + [('solution', 'sanitized'), ('solution', 'wrong-contract')]:
            folder = work / (mode + '-' + role + '-' + kind)
            shutil.copytree(root / pack / role, folder)
            if kind == 'wrong-contract':
                path = folder / 'baseline.c'
                before = path.read_text()
                old = 'int compiled_signed_compare(int8_t value, int threshold) {\n    return value < threshold;\n}' if mode == 'promotions' else 'uint64_t compiled_plain(uint64_t *left, uint64_t *right, uint64_t delta) {\n    *left += delta;\n    *right ^= *left;\n    return *left;\n}'
                new = old.replace('return value < threshold;', 'return (uint8_t)value < threshold;') if mode == 'promotions' else 'uint64_t compiled_plain(uint64_t *left, uint64_t *right, uint64_t delta) {\n    uint64_t cached = *left + delta;\n    *left = cached;\n    *right ^= cached;\n    return cached;\n}'
                assert before.count(old) == 1
                path.write_text(before.replace(old, new, 1))
            optimize = '-O0' if kind == 'O0' else '-O1' if kind == 'sanitized' else '-O2'
            flags = optimize + ' -g' + (' -DNDEBUG' if kind != 'O0' else '')
            if kind == 'sanitized':
                flags += ' -fsanitize=address,undefined -fno-sanitize-recover=undefined'
            run(['cmake', '-S', '.', '-B', 'build', '-DCMAKE_BUILD_TYPE=Debug', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                 '-DCMAKE_C_COMPILER=' + cc, '-DCMAKE_ASM_COMPILER=' + cc, '-DCMAKE_C_FLAGS_DEBUG=' + flags], folder, 'configure')
            run(['cmake', '--build', 'build', '--verbose', '--parallel', '1'], folder, 'build')
            valid = kind != 'wrong-contract'
            run(['ctest', '--test-dir', 'build', '--output-on-failure'], folder, 'ctest', expected=0 if valid else None)
            contracts = folder / 'build/contracts'
            app = folder / 'build/app'
            output, error = run([contracts], folder, 'contracts', expected=0 if valid else 1)
            assert (output == b'compiler observation contracts passed: 10269\n' and not error) if valid else b'Mismatch' in error
            out, err = run([contracts, '--rows'], folder, 'oracle-rows', stdin=payload)
            lines = out.decode().splitlines()
            assert len(lines) == len(inputs) and not err
            mismatches = 0
            for text, expected_values in zip(lines, expected_rows):
                columns = text.split()
                assert len(columns) == 6 and columns[0] == '1'
                actual = list(map(lambda value: int(value, 16), columns[1:]))
                mismatches += actual != expected_values
            assert mismatches == 0 if valid else mismatches > 0
            for changed in (False, True):
                left, right = demo_inputs(mode, changed)
                demo, demo_error = run([app] + (['--changed'] if changed else []), folder, 'demo-changed' if changed else 'demo-default', expected=0 if valid or changed else 78)
                if valid or changed:
                    rows = demo.decode().splitlines()
                    assert rows[0] == f'initial={left:016x} incoming={right:016x}' and not demo_error
                    assert [int(row.split('=')[1], 16) for row in rows[1:]] == model(mode, left, right)
            run([app, '--unsupported'], folder, 'unsupported-app', expected=64)
            run([contracts, '--unsupported'], folder, 'unsupported-contracts', expected=64)
            for invalid_index, invalid in enumerate((b'1 invalid\n', b'10000000000000000 1\n', b'-1 1\n', b'1\n', b'1 0x1\n', b'1 2 3')):
                run([contracts, '--rows'], folder, 'invalid-row-' + str(invalid_index), stdin=invalid, expected=64)
            run(['objdump', '-drwC', '-M', 'intel', app], folder, 'linked-disassembly')
            run(['readelf', '-hWs', app], folder, 'linked-elf')
            for name in ('baseline.c', 'operation.c'):
                obj = folder / ('build/CMakeFiles/app.dir/' + name + '.o')
                assert obj.read_bytes().startswith(b'\x7fELF')
                run(['objdump', '-drwC', '-M', 'intel', obj], folder, name + '-object-disassembly')
            row = dict(mode=mode, pack=pack, role=role, kind=kind, optimization=optimize,
                       directory=str(folder.relative_to(args.proof.parent)), cases=len(inputs), mismatches=mismatches,
                       actualRows='oracle-rows.stdout.txt', inputRows='oracle-rows.stdin.txt',
                       actualRowsSha256=hashlib.sha256(out).hexdigest(), inputRowsSha256=hashlib.sha256(payload).hexdigest(),
                       workingBaseline=valid, worksheetCompletionNotInferred=True,
                       sourceFiles={name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in ROLE_FILES})
            if kind in ('O0', 'O2'):
                generated = folder / 'generated.s'
                run([cc, '-std=c17', optimize, '-g', '-S', '-masm=intel', '-fverbose-asm', 'baseline.c', '-o', generated], folder, 'generate-assembly')
                run([cc, '-std=c17', optimize, '-g', '-Wall', '-Wextra', '-Wpedantic', '-Wconversion', '-Werror',
                     'tests.c', 'model.c', 'operation.c', 'abi_checks.S', generated, '-o', 'generated-contracts'], folder, 'assemble-listing')
                regenerated, regenerated_error = run([folder / 'generated-contracts', '--rows'], folder, 'generated-oracle-rows', stdin=payload)
                assert regenerated == out and not regenerated_error
                row['generatedAssemblyExecuted'] = True
                row['generatedAssemblySha256'] = hashlib.sha256(generated.read_bytes()).hexdigest()
                symbols = ('compiled_signed_compare', 'compiled_unsigned_compare') if mode == 'promotions' else ('compiled_plain', 'compiled_restricted')
                debug_path = folder / 'debugger.json'
                debug_code = '''import gdb, json
symbols = SYMBOLS
mode = MODE
target = TARGET
exits = []
gdb.events.exited.connect(lambda event: exits.append(event.exit_code))
gdb.execute("set pagination off")
gdb.execute("set confirm off")
gdb.execute("set disassembly-flavor intel")
for symbol in symbols: gdb.Breakpoint("*" + symbol, temporary=True)
gdb.execute("run")
records = []
for _ in symbols:
    name = gdb.newest_frame().name()
    assert name in symbols and name not in [row["function"] for row in records]
    reg = lambda name: int(gdb.parse_and_eval("$" + name)) & ((1 << 64) - 1)
    inferior = gdb.selected_inferior()
    readword = lambda address: int.from_bytes(bytes(inferior.read_memory(address, 8)), "little")
    entry_sp = reg("rsp"); return_pc = readword(entry_sp)
    left, right = reg("rdi"), reg("rsi")
    row = {"function": name, "entryPC": reg("pc"), "entrySP": entry_sp, "returnPC": return_pc,
           "argumentRegisters": [reg("rdi"), reg("rsi"), reg("rdx")], "steps": []}
    if mode == "aliasing": row["initialMemory"] = [readword(left), readword(right)]
    for step in range(256):
        instruction = gdb.selected_frame().architecture().disassemble(reg("pc"), count=1)[0]["asm"]
        snapshot = {"pc": reg("pc"), "instruction": instruction,
                    "registers": {r: reg(r) for r in ("rax", "rdi", "rsi", "rdx", "rsp", "rbp", "eflags")}}
        if mode == "aliasing": snapshot["memory"] = [readword(left), readword(right)]
        row["steps"].append(snapshot)
        returning = instruction.strip().split()[0] in ("ret", "retq")
        gdb.execute("stepi", to_string=True)
        if returning: break
    else: raise AssertionError("No bounded function return")
    row.update(result=reg("rax"), callerPC=reg("pc"), callerSP=reg("rsp"))
    assert row["callerPC"] == return_pc and row["callerSP"] == entry_sp + 8
    if mode == "aliasing": row["finalMemory"] = [readword(left), readword(right)]
    records.append(row)
    gdb.execute("continue")
assert exits == [0]
with open(target, "w") as stream: json.dump(records, stream, indent=2)
'''.replace('SYMBOLS', repr(symbols)).replace('MODE', repr(mode)).replace('TARGET', repr(str(debug_path)))
                script = folder / 'debugger.gdb'
                script.write_text('python\n' + debug_code + '\nend\n')
                run(['gdb', '--batch', '--nx', '-q', '-x', script, app], folder, 'debugger')
                traces = json.loads(debug_path.read_text())
                assert {trace['function'] for trace in traces} == set(symbols)
                for trace in traces:
                    assert trace['steps'] and trace['callerPC'] == trace['returnPC'] and trace['callerSP'] == trace['entrySP'] + 8
                    if mode == 'promotions':
                        assert trace['argumentRegisters'][0] & 255 == 128
                        assert trace['argumentRegisters'][1] & 0xffffffff == 0
                        assert trace['result'] & 0xffffffff == int(trace['function'] == 'compiled_signed_compare')
                    elif trace['function'] == 'compiled_plain':
                        assert trace['argumentRegisters'][2] == 5
                        assert trace['argumentRegisters'][0] == trace['argumentRegisters'][1]
                        assert trace['initialMemory'] == [3, 3] and trace['finalMemory'] == [0, 0] and trace['result'] == 0
                    else:
                        assert trace['argumentRegisters'][2] == 5
                        assert trace['argumentRegisters'][1] - trace['argumentRegisters'][0] == 8
                        assert trace['initialMemory'] == [3, 5] and trace['finalMemory'] == [8, 13] and trace['result'] == 8
                proof['debuggerTraces'].append(dict(mode=mode, role=role, kind=kind, path=str(debug_path.relative_to(args.proof.parent)),
                                                   sha256=hashlib.sha256(debug_path.read_bytes()).hexdigest(), functions=2,
                                                   instructionSteps=sum(len(trace['steps']) for trace in traces)))
            proof['profiles'].append(row)
    assert sources == {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources}
    proof.update(nativeExecuted=True, ordinaryUser=True, exactSourceFilesUnchanged=True,
                 everyRestrictedCallUsesDistinctModifiedObjects=True, undefinedAliasCallsNeverExecuted=True,
                 suppliedStartersWorkAndRequireWorksheetEvidence=True)
    args.proof.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(dict(profiles=len(proof['profiles']), debuggerTraces=len(proof['debuggerTraces']),
                          compiler=args.cc, sourceFiles=len(sources), nativeExecuted=True)))


if __name__ == '__main__':
    main()
