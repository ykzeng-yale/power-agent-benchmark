#!/usr/bin/env python3
"""Question-only, prospectively frozen post-study release2.1.2 regression.

No oracle, source answer or benchmark scorer belongs in this image. Scoring is
performed separately after the original responses are downloaded. The budget
guard stops dispatch on observed spend or projected full-study spend; bounded
in-flight calls can still complete after a stop and are always preserved.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import pathlib
import random
import statistics
import subprocess
import tempfile
import threading
import time

MODEL = 'claude-haiku-4-5-20251001'
CORE = ['scientific-harness-cli.js', 'scientific-harness.js',
        'scientific-r-executor.js', 'scientific-r-worker.py', 'model-config.js', 'scientific-reference-guard.js']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix('.partial')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def usd(record):
    usage = record.get('usage', {})
    return (usage.get('input_tokens', 0)+5*usage.get('output_tokens', 0))/1e6+record.get('missing_usage_cost_assumed_usd', 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--questions', type=pathlib.Path, default=pathlib.Path('/app/replication-questions.json'))
    parser.add_argument('--cli', type=pathlib.Path, default=pathlib.Path('/app/scientific-harness-cli.js'))
    parser.add_argument('--out', type=pathlib.Path, default=pathlib.Path('/study'))
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--budget-usd', type=float, default=15.0)
    parser.add_argument('--gcs-prefix')
    args = parser.parse_args()
    if args.workers < 1 or args.budget_usd <= 0:
        parser.error('Workers and budget must be positive')
    payload = json.loads(args.questions.read_text())
    tasks = payload['tasks']
    if len(tasks) != 20 or len({t.get('id') for t in tasks}) != 20 or any(set(t) != {'id', 'query'} or not isinstance(t['query'],str) or not t['query'].strip() for t in tasks):
        raise ValueError('Expected exactly twenty question-only task payloads')
    jobs = [{'task_id': t['id'], 'mode': mode, 'repeat': 1} for t in tasks for mode in ['single', 'multi']]
    random.Random(20261004).shuffle(jobs)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'transport').mkdir(exist_ok=True)
    os.chmod(args.out/'transport',0o700)
    os.chmod(args.out, 0o700)  # R's unprivileged user cannot read study payload/records.
    if (args.out/'protocol.json').exists():
        raise ValueError('Refusing to overwrite a frozen replication')
    hashes = {str(args.cli.with_name(name)): sha(args.cli.with_name(name)) for name in CORE}
    expected = json.loads(args.cli.with_name('regression-release-manifest.json').read_text())['core_sha256']
    if {pathlib.Path(name).name:digest for name,digest in hashes.items()} != expected:
        raise ValueError('Backend core differs from prospective release manifest')
    image = os.environ.get('POWER_AGENT_STUDY_IMAGE_DIGEST','')
    if '@sha256:' not in image or len(image.rsplit('@sha256:',1)[-1]) != 64:
        raise ValueError('Exact immutable study-image digest required')
    initial_forecast = {'single': .07, 'multi': .18}  # Conservative observed Mac pilot means; not answers.
    protocol = {
        'cohort': 'Separately prospectively frozen release2.1.2 current-production regression; same developer-exposed20 tasks',
        'version': '2.1.2', 'runner_version': 'release-regression-1', 'backend_base_image_digest': 'gcr.io/power-agent-476822/power-agent-api@sha256:c7744480a44406e7d92189d13300458481cc91a07adb227986090bc5f0170581', 'study_image_digest': os.environ.get('POWER_AGENT_STUDY_IMAGE_DIGEST'), 'scoring': 'Unchanged audited suite2.0.0 oracles and null-safe2.0.1 scorer, entirely offline after raw retrieval', 'frozen_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'model': MODEL, 'task_payload_sha256': sha(args.questions), 'runner_sha256': sha(pathlib.Path(__file__)),
        'source_core_protocol_sha256': payload['source_core_protocol_sha256'],
        'source_question_contract_sha256': payload['source_question_contract_sha256'],
        'jobs': jobs, 'planned_attempts': 40, 'repeats': 1, 'workers': args.workers,
        'randomization_seed': 20261004, 'hashes': hashes,
        'budgets': {'model_calls': 18, 'executions': 8, 'repairs': 1, 'deadline_seconds': 300,
                    'total_dispatch_budget_usd': args.budget_usd, 'initial_forecast_usd_per_mode': initial_forecast},
        'budget_rule': 'Before dispatch, stop remaining jobs when observed cost or projected full-study cost reaches budget. Projection uses max(initial forecast, observed mean) per mode. In-flight bounded calls finish and count; final provider billing is not a guaranteed hard dollar cap.',
        'usage_qualification': 'Uncached $1input/$5output per million-token estimate only; provider failures with missing usage are unknown and forecast imputations are dispatch-only, not billing.',
        'analysis': 'Every forty planned attempt counts. Local scoring after download uses the original frozen core oracle/scorer; unscheduled budget stops count as failures. Report separately from allfour earlier cohorts. This is a developer-exposed post-study release regression, not a blind holdout or causal cross-version improvement estimate. No replacement or pooled claim.',
        'isolation': 'Prospective immutable Linux image with restricted unprivileged R worker; no benchmark oracle mounted. Execution environment differs from the Mac pilot.'}
    write_json(args.out/'protocol.json', protocol)
    write_json(args.out/'public-questions.json', payload)
    print(json.dumps({'event': 'protocol_frozen', 'planned_attempts': len(jobs), 'protocol_sha256': sha(args.out/'protocol.json'), 'budget_usd': args.budget_usd}), flush=True)

    def upload(paths, subdirectory=''):
        if not args.gcs_prefix:
            return
        transfer = subprocess.run(['gsutil', '-m', 'cp', *[str(p) for p in paths], args.gcs_prefix.rstrip('/')+'/'+subdirectory],
                                  text=True, capture_output=True, timeout=60)
        if transfer.returncode:
            raise RuntimeError('Artifact upload failed: '+transfer.stderr[-300:])

    # Persist the prospective protocol before spending API tokens, and each
    # response immediately, so an interrupted ephemeral Cloud Run job cannot
    # lose earlier attempts. Upload failure stops new dispatch, not scoring.
    upload([args.out/'protocol.json', args.out/'public-questions.json'])
    queries = {t['id']: t['query'] for t in tasks}
    lock = threading.Lock()
    completed, active, pending = [], [], list(jobs)
    stop_reason = None

    def forecast():
        rates = {}
        for mode in ['single', 'multi']:
            known = [usd(r['record']) for r in completed if r['mode'] == mode and r['record'].get('status') != 'budget_not_started']
            rates[mode] = max(initial_forecast[mode], statistics.mean(known)) if known else initial_forecast[mode]
        spent = sum(usd(r['record']) for r in completed)
        return spent, spent+sum(rates[j['mode']] for j in active+pending)

    def run(job):
        nonlocal stop_reason
        started = time.monotonic()
        with lock:
            spent, predicted = forecast()
            if spent >= args.budget_usd or predicted > args.budget_usd:
                stop_reason = 'observed_or_projected_dispatch_cost_limit'
            pending.remove(job)
            if stop_reason:
                record = {'status': 'budget_not_started', 'scientificStatus': 'budget_not_started', 'success': False, 'error': stop_reason, 'usage': {}}
            else:
                active.append(job)
                record = None
        if record is None:
            try:
                if {name: sha(pathlib.Path(name)) for name in hashes} != hashes:
                    raise ValueError('Frozen harness source changed')
                request = {'query': queries[job['task_id']], 'workflowMode': job['mode'],
                           'maxModelCalls': 18, 'maxExecutions': 8, 'maxRepairs': 1, 'deadlineMs': 300000}
                with tempfile.TemporaryDirectory(prefix='linux-pa26-') as working:
                    proc = subprocess.run(['node', str(args.cli), '--mode', job['mode'], '--deadline-ms', '300000'],
                                          input=json.dumps(request), text=True, capture_output=True,
                                          cwd=working, timeout=330)
                transport_capture={'task_id':job['task_id'],'mode':job['mode'],'repeat':job['repeat'],
                                   'stdout':proc.stdout,'stderr':proc.stderr,'exit_code':proc.returncode}
                secret=os.environ.get('ANTHROPIC_API_KEY')
                serialized_capture=json.dumps(transport_capture)
                if secret and secret in serialized_capture:
                    transport_capture=json.loads(serialized_capture.replace(secret,'[REDACTED_ENV_SECRET]'))
                    transport_capture['secret_redaction_applied']=True
                capture_path=args.out/'transport'/f"{job['task_id']}__{job['mode']}__r1.transport.json"
                write_json(capture_path,transport_capture)  # raw process capture before JSON parsing/scoring
                try:
                    upload([capture_path], 'transport/')
                except Exception:
                    with lock:
                        stop_reason='artifact_upload_failed_stop_dispatch'
                if proc.returncode:
                    raise RuntimeError('provider_process_error: '+proc.stderr[-500:])
                record = json.loads(proc.stdout)
                if not isinstance(record,dict):
                    raise ValueError('Provider stdout is not a record object; raw transport retained')
                if record.get('model') != MODEL or record.get('harnessVersion') != '2.1.2' or {name: sha(pathlib.Path(name)) for name in hashes} != hashes:
                    record['evaluation_version_changed'] = True
            except subprocess.TimeoutExpired as error:
                def decoded(value):
                    return value.decode('utf8','replace') if isinstance(value,bytes) else (value or '')
                partial={'task_id':job['task_id'],'mode':job['mode'],'repeat':job['repeat'],
                         'stdout':decoded(error.stdout),'stderr':decoded(error.stderr),'exit_code':None,'timed_out':True}
                secret=os.environ.get('ANTHROPIC_API_KEY'); serialized_partial=json.dumps(partial)
                if secret and secret in serialized_partial:
                    partial=json.loads(serialized_partial.replace(secret,'[REDACTED_ENV_SECRET]'))
                    partial['secret_redaction_applied']=True
                capture_path=args.out/'transport'/f"{job['task_id']}__{job['mode']}__r1.transport.json"
                write_json(capture_path,partial)
                try:
                    upload([capture_path], 'transport/')
                except Exception:
                    with lock:
                        stop_reason='artifact_upload_failed_stop_dispatch'
                record={'status':'provider_error','scientificStatus':'provider_error','success':False,
                        'error':'provider_process_timeout; partial stdout/stderr retained; model terminal status unknown',
                        'usage':{},'missing_usage_cost_assumed_usd':max(.25,2*initial_forecast[job['mode']]),
                        'usage_note':'Missing provider usage is unknown; imputation only supports dispatch forecasting.'}
            except Exception as error:
                record = {'status': 'provider_error', 'scientificStatus': 'provider_error', 'success': False, 'error': str(error), 'usage': {},
                          'missing_usage_cost_assumed_usd': max(.25, 2*initial_forecast[job['mode']]),
                          'usage_note': 'Provider failed without usage; conservative forecast cost is imputed for budget dispatch, not claimed as billed tokens.'}
        # Only known env-secret values are redacted, without printing or exporting them.
        serialized = json.dumps(record)
        key = os.environ.get('ANTHROPIC_API_KEY')
        if key and key in serialized:
            record = json.loads(serialized.replace(key, '[REDACTED_ENV_SECRET]'))
            record['secret_redaction_applied'] = True
        result = dict(job, record=record, duration_seconds=round(time.monotonic()-started, 3))
        result_path = args.out/f"{job['task_id']}__{job['mode']}__r1.json"
        write_json(result_path, result)
        upload_error = None
        try:
            upload([result_path])
        except Exception as error:
            upload_error = str(error)
            with lock:
                stop_reason = 'artifact_upload_failed_stop_dispatch'
        with lock:
            if job in active:
                active.remove(job)
            completed.append(result)
            spent, projected = forecast()
            progress = {'event': 'attempt_recorded', **job, 'status': record.get('status'),
                        'recorded_attempts': len(completed), 'planned_attempts': 40,
                        'duration_seconds': result['duration_seconds'], 'usage': record.get('usage', {}),
                        'observed_usd': round(spent, 6), 'projected_total_usd': round(projected, 6),
                        'artifact_upload_error': upload_error}
        print(json.dumps(progress), flush=True)
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    summary = {'cohort': protocol['cohort'], 'protocol_sha256': sha(args.out/'protocol.json'),
               'planned_attempts': 40, 'recorded_attempts': len(completed), 'budget_stop_reason': stop_reason,
               'estimated_token_cost_usd': sum((r['record'].get('usage',{}).get('input_tokens',0)+5*r['record'].get('usage',{}).get('output_tokens',0))/1e6 for r in completed),
               'dispatch_forecast_cost_usd_including_imputed_unknown_usage': sum(usd(r['record']) for r in completed),
               'usage_missing_attempts':[{k:r[k] for k in ('task_id','mode','repeat')} for r in completed if r['record'].get('missing_usage_cost_assumed_usd')], 'records': completed}
    write_json(args.out/'records.json', summary)
    if args.gcs_prefix:
        files = sorted(args.out.glob('*.json'))
        upload(files)
        print(json.dumps({'event': 'gcs_upload', 'success': True, 'prefix': args.gcs_prefix,
                          'artifact_count': len(files)}), flush=True)
    print(json.dumps({'event': 'study_completed', 'planned_attempts': 40, 'recorded_attempts': len(completed),
                      'estimated_token_cost_usd': summary['estimated_token_cost_usd'], 'budget_stop_reason': stop_reason}), flush=True)


if __name__ == '__main__':
    main()
