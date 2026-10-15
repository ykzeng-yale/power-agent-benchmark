#!/usr/bin/env python3
"""Question-only runner. This file never opens scientific reference files.

The preparation/scoring programs are separate. Only exact frozen question text
and matched configuration reach the CLI. Full raw bytes are persisted before
JSON parsing. No outcome replacements, selective reruns, or automatic resume.
"""
import argparse
import base64
import concurrent.futures
import datetime
import hashlib
import json
import os
import pathlib
import signal
import subprocess
import tempfile
import time

VERSION = 'prospective-numerical-dispatch1-api2.4.3'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def encoded(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def dump(p, value):
    p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    p.parent.chmod(0o700)
    tmp = p.with_suffix(p.suffix + '.partial')
    with open(tmp, 'w', opener=lambda path, flags: os.open(path, flags, 0o600)) as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(p)
    p.chmod(0o600)

def strict_json(text):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('duplicate_json_key')
            result[k] = v
        return result
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))

def check_hashes(directory, hashes):
    return all((directory / name).is_file() and sha(directory / name) == value for name, value in hashes.items())

def make_request(protocol, questions, job):
    # No ID, tier, source locator, reference path/value, or output-contract
    # appendix is appended here. The earlier frozen query already contains its
    # exact structured reporting instruction.
    return dict(protocol['common'], query=questions[job['question_index']]['query'], workflowMode=job['mode'])

def execute_job(job, request, cli, node, out, protocol_sha, runtime_hashes, timeout_extra=30):
    started = time.monotonic()
    stdout = stderr = b''
    code = None
    failure = None
    dispatched = False
    raw = out / 'transports' / (job['job_id'] + '.transport.json')
    parsed_path = out / 'attempts' / (job['job_id'] + '.json')
    if raw.exists() or parsed_path.exists():
        raise RuntimeError('refuse_attempt_overwrite')
    try:
        if not check_hashes(cli.parent, runtime_hashes):
            raise RuntimeError('frozen_runtime_changed_before_dispatch')
        with tempfile.TemporaryDirectory(prefix='pa-question-only-') as td:
            # A fresh process/cwd prevents conversation reuse. It is not an OS
            # filesystem sandbox; private local files remain out of model
            # messages, but are not claimed inaccessible to arbitrary R code.
            p = subprocess.Popen([node, str(cli), '--mode', job['mode'], '--deadline-ms', str(request['deadlineMs'])],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 cwd=td, start_new_session=True)
            dispatched = True
            try:
                stdout, stderr = p.communicate(encoded(request), timeout=request['deadlineMs'] / 1000 + timeout_extra)
            except subprocess.TimeoutExpired:
                failure = 'process_deadline_exceeded'
                os.killpg(p.pid, signal.SIGTERM)
                try:
                    stdout, stderr = p.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    stdout, stderr = p.communicate()
            code = p.returncode
    except Exception as error:
        # Error class/reason only; no environment values or command headers.
        failure = str(error) if isinstance(error, RuntimeError) else type(error).__name__
    duration = round(time.monotonic() - started, 3)
    transport = dict(job, dispatched=dispatched, captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     protocol_sha256=protocol_sha, request_sha256=hashlib.sha256(encoded(request)).hexdigest(),
                     exit_code=code, runner_failure=failure, duration_seconds=duration,
                     stdout_base64=base64.b64encode(stdout).decode(), stderr_base64=base64.b64encode(stderr).decode(),
                     stdout_sha256=hashlib.sha256(stdout).hexdigest(), stderr_sha256=hashlib.sha256(stderr).hexdigest())
    dump(raw, transport)  # Durable raw-first receipt BEFORE any response parsing.
    record = None
    parse_error = None
    try:
        record = strict_json(stdout.decode('utf-8'))
        if not isinstance(record, dict):
            raise ValueError('response_not_object')
    except Exception as error:
        record = None
        parse_error = type(error).__name__
    row = dict(job, dispatched=dispatched, transport_captured=True, transport_sha256=sha(raw),
               protocol_sha256=protocol_sha, duration_seconds=duration, record=record,
               capture_error=parse_error, process_error=failure, exit_code=code,
               runtime_changed=not check_hashes(cli.parent, runtime_hashes))
    dump(parsed_path, row)
    return row

def dispatch(protocol_path, question_path, cli, node, out):
    protocol = strict_json(protocol_path.read_bytes())
    questions = strict_json(question_path.read_bytes())
    if protocol.get('state') != 'frozen' or not protocol.get('independent_review_receipt_sha256'):
        raise RuntimeError('a_reviewed_frozen_protocol_is_required')
    if sha(question_path) != protocol['question_payload_sha256']:
        raise RuntimeError('question_payload_changed')
    if not check_hashes(protocol_path.parent, protocol['adapter_files']):
        raise RuntimeError('frozen_adapter_changed')
    if not check_hashes(cli.parent, protocol['runtime_files']):
        raise RuntimeError('frozen_runtime_changed')
    receipt = protocol_path.parent / 'independent-review-receipt.json'
    if not receipt.is_file() or sha(receipt) != protocol['independent_review_receipt_sha256']:
        raise RuntimeError('review_receipt_changed')
    if out.exists():
        raise RuntimeError('refuse_restart_or_output_overwrite')
    out.mkdir(mode=0o700, parents=True)
    dump(out / 'started.json', {'protocol_sha256': sha(protocol_path), 'planned_attempts': len(protocol['jobs']),
                               'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    (out / 'protocol.json').write_bytes(protocol_path.read_bytes())
    (out / 'protocol.json').chmod(0o600)
    records = []
    workers = protocol['workers']
    if workers != 2:
        raise RuntimeError('this_protocol_requires_concurrency_two')
    # At most two tasks active. Scheduling order is frozen before observations;
    # stopping/interruption leaves absent jobs in the planned denominator.
    pending = {}
    iterator = iter(protocol['jobs'])
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            while True:
                while len(pending) < workers:
                    try:
                        job = next(iterator)
                    except StopIteration:
                        break
                    req = make_request(protocol, questions, job)
                    f = pool.submit(execute_job, job, req, cli, node, out, sha(protocol_path), protocol['runtime_files'])
                    pending[f] = job
                if not pending:
                    break
                done, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
                for f in done:
                    job = pending.pop(f)
                    try:
                        row = f.result()
                    except Exception as error:
                        # Preserve failures that prevent normal capture as an
                        # explicit planned failure; never replace its response.
                        raw = out / 'transports' / (job['job_id'] + '.transport.json')
                        row = dict(job, dispatched=None, transport_captured=raw.exists(), record=None,
                                   protocol_sha256=sha(protocol_path), capture_error=type(error).__name__,
                                   model_status_unknown=True)
                        if raw.exists():
                            row['transport_sha256'] = sha(raw)
                        dump(out / 'attempts' / (job['job_id'] + '.json'), row)
                    records.append(row)
                    dump(out / 'progress.json', {'captured': len(records), 'planned': len(protocol['jobs']),
                                                 'active': len(pending), 'last_job_id': job['job_id']})
                    print(json.dumps({'captured': len(records), 'planned': len(protocol['jobs']),
                                      'job_id': job['job_id'], 'status': (row.get('record') or {}).get('scientificStatus'),
                                      'capture_error': row.get('capture_error')}), flush=True)
    finally:
        seen = {r['job_id'] for r in records}
        for job in protocol['jobs']:
            if job['job_id'] not in seen:
                records.append(dict(job, dispatched=False, transport_captured=False, record=None,
                                    protocol_sha256=sha(protocol_path), operational_status='not_captured_at_runner_exit'))
        order = {job['job_id']: i for i, job in enumerate(protocol['jobs'])}
        records.sort(key=lambda row: order[row['job_id']])
        dump(out / 'records.json', {'runner_version': VERSION, 'protocol_sha256': sha(protocol_path),
                                    'planned_attempts': len(protocol['jobs']), 'records': records})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--protocol', type=pathlib.Path, required=True)
    ap.add_argument('--questions', type=pathlib.Path, required=True)
    ap.add_argument('--cli', type=pathlib.Path, required=True)
    ap.add_argument('--node', default='node')
    ap.add_argument('--out', type=pathlib.Path, required=True)
    a = ap.parse_args()
    dispatch(a.protocol.resolve(), a.questions.resolve(), a.cli.resolve(), a.node, a.out.resolve())

if __name__ == '__main__':
    main()
