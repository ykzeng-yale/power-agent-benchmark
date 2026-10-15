#!/usr/bin/env python3
"""Score downloaded Linux records locally; never put this or oracles in image."""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('frozen_score', ROOT/'runner/audited_benchmark_v2_0_1.py')
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run_directory', type=pathlib.Path)
    args = parser.parse_args()
    folder = args.run_directory
    protocol_path = folder/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    if protocol['planned_attempts'] != 40 or len(protocol['jobs']) != 40:
        raise ValueError('Unexpected prospectively planned denominator')
    payload = json.loads((folder/'public-questions.json').read_text())
    if hashlib.sha256((folder/'public-questions.json').read_bytes()).hexdigest() != protocol['task_payload_sha256']:
        raise ValueError('Question payload hash does not match prospective protocol')
    tasks = json.loads((ROOT/'audited/tasks.json').read_text())['tasks']
    if {t['id']: t['query'] for t in payload['tasks']} != {t['id']: scorer.public_request(t, 'single')['query'] for t in tasks}:
        raise ValueError('Linux provider questions differ from frozen core public requests')
    oracle = {o['id']: o for o in json.loads((ROOT/'audited/oracles.json').read_text())['tasks']}
    rows = [json.loads(f.read_text()) for f in sorted(folder.glob('pa26*json'))]
    by_key = {(r['task_id'], r['mode'], r['repeat']): r for r in rows}
    if len(by_key) != len(rows):
        raise ValueError('Duplicated raw attempts')
    planned = {(j['task_id'], j['mode'], j['repeat']) for j in protocol['jobs']}
    if set(by_key)-planned:
        raise ValueError('Unscheduled extra responses cannot be included')
    if set(by_key) != planned:
        raise ValueError('Cohort incomplete: retain missing identities separately; do not manufacture provider records')
    scored = []
    for job in protocol['jobs']:
        row = by_key[(job['task_id'], job['mode'], job['repeat'])]
        scored.append(dict(row, evaluation=scorer.score(row['record'], oracle[row['task_id']])))
    # Conventional median is derived from observed durations, without imputing
    # zero-duration observations for records that omit elapsed time.
    for_summary = [dict(r, duration_seconds=r['duration_seconds'] or 0) for r in scored]
    summary = scorer.summarize(for_summary, tasks)
    for mode in ['single', 'multi']:
        observed = [r['duration_seconds'] for r in scored if r['mode'] == mode and r['duration_seconds'] is not None]
        summary[mode]['median_seconds'] = statistics.median(observed) if observed else None
        summary[mode]['latency_observed_attempts'] = len(observed)
        summary[mode]['numeric_agreement_all_planned'] = sum(r['evaluation']['numeric_pass'] for r in scored if r['mode'] == mode)
        summary[mode]['completed_numeric_agreement'] = sum(r['evaluation']['numeric_pass'] and r['record'].get('status') == 'completed' for r in scored if r['mode'] == mode)
    result = {'cohort': protocol['cohort'], 'harness_version': protocol['version'], 'suite_version': '2.0.0', 'scoring_version': '2.0.1-null-safe',
              'protocol_sha256': hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
              'planned_attempts': 40, 'raw_recorded_attempts': len(rows), 'missing_attempts_counted_as_failure': 40-len(rows),
              'summary': summary, 'records': scored,
              'analysis_note': 'Separately prospectively frozen Linux replication. Immutable worker/R4.4.1 differs from the Mac prototype. No pooling, no replacement. Original numeric/design/evidence gates and oracles used locally with a declared null-safe schema wrapper; valid-record judgments unchanged. Conventional latency median is a derived correction to the frozen runner upper-middle summary convention.'}
    destination = folder/'scored-results.json'
    if destination.exists():
        raise ValueError('Refusing to overwrite derived scored evidence')
    destination.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], indent=2))


if __name__ == '__main__':
    main()
