#!/usr/bin/env python3
"""Derived publication summaries; frozen scores/records are never overwritten.

Missing capture jobs are represented only in planned-job accounting. Their model
status and usage remain unknown. Bootstrap intervals are descriptive, not tests
of general capability. Merging constructed variants is a post-hoc dependence
sensitivity analysis and does not change the declared primary scores.
"""
import collections
import csv
import datetime
import hashlib
import importlib.util
import json
import pathlib
import random
import statistics

ROOT = pathlib.Path(__file__).resolve().parents[1]
MERGES = {
    'constructed-rm-between': 'verma7.6',
    'constructed-riley-binary': 'pms-manual-binary',
    'constructed-cluster-rate': 'fieldtrials5.6.1',
}
COHORTS = [
    ('linux40', 'haiku-linux-replication-20261001', 'scored-results.json', False),
    ('mac120', 'haiku-v2-20261001', 'derived-accounting.json', False),
    ('original_extension24', 'haiku-source-extension-20261001', 'derived-accounting.json', True),
    ('corrected_extension24', 'haiku-source-extension-v2_0_1-20261001', 'results.json', True),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(job):
    return job['task_id'], job['mode'], job['repeat']


def bootstrap(values, family_by, merged=False):
    """Resample whole labels; weight tasks equally as in frozen primary runner."""
    groups = collections.defaultdict(list)
    for task_id in sorted(values):
        family = family_by[task_id]
        if merged:
            family = MERGES.get(family, family)
        groups[family].append(values[task_id])
    clusters = list(groups.values())
    if not clusters:
        return {'estimate': None, 'family_count': 0, 'interval95': [None, None]}
    rng = random.Random(20261001)
    draws = []
    for _ in range(10000):
        sampled = [v for _ in clusters for v in rng.choice(clusters)]
        draws.append(sum(sampled)/len(sampled))
    draws.sort()
    return {'estimate': sum(values.values())/len(values), 'family_count': len(clusters),
            'interval95': [draws[249], draws[9749]]}


def indicator(row, metric):
    if row is None:
        return False
    evaluation = row['evaluation']
    if metric == 'strict':
        return evaluation['passed']
    if metric == 'numerical_agreement':
        return evaluation.get('numeric_pass', False)
    if metric == 'completed_numerical_agreement':
        return (evaluation.get('numeric_pass', False)
                and row['record'].get('scientificStatus', row['record'].get('status')) == 'completed'
                and row['record'].get('success') is True)
    raise ValueError(metric)


def summarize_cohort(name, folder, source, extension):
    protocol_path = folder/'protocol.json'
    source_path = folder/source
    if not source_path.exists():
        return None
    protocol = json.loads(protocol_path.read_text())
    analysis = json.loads(source_path.read_text())
    rows = analysis['records']
    observed = {key(row): row for row in rows}
    planned = protocol['jobs']
    if len(observed) != len(rows) or set(observed)-{key(j) for j in planned}:
        raise ValueError('Duplicate or unplanned provider record')
    missing = [j for j in planned if key(j) not in observed]
    if source == 'results.json' and missing:
        raise ValueError('Corrected cohort not complete')
    tasks_path = ROOT/('cohorts/source-extension/audited/tasks.json' if extension else 'audited/tasks.json')
    task_by = {t['id']: t for t in json.loads(tasks_path.read_text())['tasks']}
    family_by = {i: t['family'] for i, t in task_by.items()}
    modes = {}
    task_rates = {}
    plot_rows = []
    for mode in ['single', 'multi']:
        jobs = [j for j in planned if j['mode'] == mode]
        actual = [observed[key(j)] for j in jobs if key(j) in observed]
        metric_rows = {}
        task_rates[mode] = {}
        for metric in ['strict', 'numerical_agreement', 'completed_numerical_agreement']:
            rates = {}
            for task_id in sorted({j['task_id'] for j in jobs}):
                js = [j for j in jobs if j['task_id'] == task_id]
                rates[task_id] = sum(indicator(observed.get(key(j)), metric) for j in js)/len(js)
            count = sum(indicator(observed.get(key(j)), metric) for j in jobs)
            metric_rows[metric] = {'count': count, 'planned_denominator': len(jobs),
                                   'declared_labels': bootstrap(rates, family_by),
                                   'posthoc_merged_labels': bootstrap(rates, family_by, merged=True)}
            task_rates[mode][metric] = rates
            for tier in [0, 1, 2, 3, 4]:
                selected = [j for j in jobs if tier == 0 or task_by[j['task_id']]['tier'] == tier]
                if not selected:
                    continue
                selected_rates = {t: r for t, r in rates.items() if tier == 0 or task_by[t]['tier'] == tier}
                b = bootstrap(selected_rates, family_by)
                plot_rows.append({'cohort': name, 'mode': mode, 'metric': metric, 'tier': tier,
                                  'passed': sum(indicator(observed.get(key(j)), metric) for j in selected),
                                  'planned': len(selected), 'rate': b['estimate'],
                                  'lower95': b['interval95'][0], 'upper95': b['interval95'][1],
                                  'declared_families': b['family_count']})
        usage = {k: sum(r['record'].get('usage', {}).get(k, 0) for r in actual)
                 for k in ['input_tokens', 'output_tokens']}
        durations = [r['duration_seconds'] for r in actual if r.get('duration_seconds') is not None]
        modes[mode] = {'planned_attempts': len(jobs), 'captured_attempts': len(actual),
                       'missing_capture_attempts': len(jobs)-len(actual),
                       'observed_statuses': dict(collections.Counter(r['record'].get('status') for r in actual)),
                       'median_observed_seconds': statistics.median(durations) if durations else None,
                       'usage_observed': usage,
                       'uncached_observed_token_cost_estimate_usd': (usage['input_tokens']+5*usage['output_tokens'])/1e6,
                       'metrics': metric_rows}
    differences = {}
    for metric in ['strict', 'numerical_agreement', 'completed_numerical_agreement']:
        delta = {t: task_rates['multi'][metric][t]-r for t, r in task_rates['single'][metric].items()}
        differences[metric] = {'declared_labels': bootstrap(delta, family_by),
                               'posthoc_merged_labels': bootstrap(delta, family_by, merged=True)}
    return ({'cohort': name, 'protocol_sha256': sha(protocol_path), 'input_analysis_sha256': sha(source_path),
             'planned_attempts': len(planned), 'raw_captured_attempts': len(rows),
             'missing_capture_jobs': missing, 'modes': modes, 'paired_multi_minus_single': differences,
             'interpretation': ('Operational pipeline including unknown capture losses; no model status/usage imputed.'
                                if missing else 'All planned responses captured; no retry/replacement or pooled cohort claim.')},
            plot_rows)


def main():
    cohorts, plot_rows = [], []
    for name, directory, source, extension in COHORTS:
        result = summarize_cohort(name, ROOT/'results'/directory, source, extension)
        if result is not None:
            cohort, rows = result
            cohorts.append(cohort)
            plot_rows.extend(rows)
    result = {'analysis_version': '1.0.0-derived',
              'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'method': '10000 whole-declared-family bootstrap draws with seed20261001; equal-task weighted means; paired modes/repeats kept together. Numeric agreement can include incomplete responses; completed numerical agreement is separately reported.',
              'dependence_sensitivity': {'posthoc': True, 'merge_map': MERGES,
                                         'note': 'Merge direct constructed variants into source/method anchors. Preserves original labels/metrics/records, not a semantic-independence guarantee. Related Gaussian methods remain dependent.'},
              'limitations': 'Selected public developer-exposed tasks; intervals are descriptive, not confirmatory general-capability inference. Linux has one attempt/task/mode and cannot estimate within-task stochastic variation. Mac shared-library mutability, initial package installation and capture losses prohibit clean scientific mode comparison.',
              'cost_note': 'Input/output tokens at Haiku4.5 uncached $1/$5 per million; estimated, not billing. Missing capture usage unknown, never zero. Native/UI calls outside these cohorts excluded.',
              'cohorts': cohorts}
    destination = ROOT/'results/publication-analysis.json'
    destination.write_text(json.dumps(result, indent=2)+'\n')
    with (ROOT/'results/publication-plot-data.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(plot_rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(plot_rows)
    print(json.dumps({c['cohort']: c['paired_multi_minus_single']['strict'] for c in cohorts}, indent=2))


if __name__ == '__main__':
    main()
