#!/usr/bin/env python3
"""Descriptive failure/evidence audit. Never changes frozen score or response."""
import argparse
import collections
import datetime
import hashlib
import json
import pathlib
import re

NETWORK = re.compile(r'\b(?:download\.file|install\.packages|curl_fetch_memory|GET|socketConnection|url)\s*\(|https?://')
FILES = re.compile(r'\b(?:readLines|read\.csv|read\.table|readRDS|read_json|source|list\.files|Sys\.getenv)\s*\(')
ORACLE = re.compile(r'audited/oracles|reference-specifications|benchmark-ground-truth|haiku-v2|pa26-t[1-4]-|legacy-audit')
SECRET = re.compile(r'sk-ant-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{25,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')


def label(row):
    return f"{row['task_id']}__{row['mode']}__r{row['repeat']}"


def categories(row):
    r, e = row['record'], row['evaluation']
    status = r.get('status')
    out = set()
    if e['passed']:
        return out
    reasons = e['reason']
    if any(k.startswith('design_') for k in reasons):
        out.add('planner_or_reporting_design_contract_mismatch')
    if any(k in reasons for k in ['missing_or_ambiguous_primary_metric', 'invalid_numeric_schema']):
        out.add('missing_or_invalid_primary_result')
    if status == 'completed' and e.get('numeric_pass') and not e['passed']:
        out.add('completed_correct_number_fails_other_gate')
    if status == 'needs_clarification':
        p = r.get('plan') or {}
        if not p.get('missing_information') and not p.get('clarification_questions'):
            out.add('planner_not_ready_without_missing_information_or_question')
        else:
            out.add('clarification_requested_on_curated_specification')
    if any(x.get('success') is False for x in r.get('executions', [])):
        out.add('failed_execution_in_terminal_failed_attempt')
    if status == 'budget_exhausted':
        role = next((x.get('role') for x in reversed(r.get('trace', [])) if x.get('role') in ['planner', 'coder', 'reviewer']), None)
        out.add('reviewer_budget_or_completion_liveness' if role == 'reviewer' else 'coder_or_other_budget_exhaustion')
    if status == 'review_failed' or (r.get('review') or {}).get('approved') is False:
        out.add('reviewer_disagreement')
    if status == 'provider_error':
        out.add('provider_error')
    if e.get('agent_value') is not None and not e.get('numeric_pass'):
        out.add('numerical_or_method_disagreement')
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run_directory', type=pathlib.Path)
    parser.add_argument('--scored-results', action='store_true', help='Read locally scored Linux records')
    parser.add_argument('--harness-dir', type=pathlib.Path, help='Verified image source directory corresponding to /app hashes')
    args = parser.parse_args()
    folder = args.run_directory
    protocol = json.loads((folder/'protocol.json').read_text())
    rows = (json.loads((folder/'scored-results.json').read_text())['records'] if args.scored_results
            else [json.loads(f.read_text()) for f in sorted(folder.glob('pa26*json'))])
    grouped = collections.defaultdict(list)
    code_findings, secret_files = [], []
    total_executions = successful_review = 0
    for row in rows:
        for c in categories(row):
            grouped[c].append(label(row))
        r = row['record']
        if SECRET.search(json.dumps(r)):
            secret_files.append(label(row))  # Never emit matching secret strings.
        for x in r.get('executions', []):
            total_executions += 1
            if x.get('role') == 'reviewer' and x.get('success'):
                successful_review += 1
            code = x.get('code', '')
            flags = [name for name, pattern in [('network_or_package_download', NETWORK),
                                                ('file_or_environment_read', FILES),
                                                ('reference_answer_store_or_task_id', ORACLE)] if pattern.search(code)]
            if flags:
                code_findings.append({'attempt': label(row), 'execution_id': x.get('id'), 'role': x.get('role'), 'flags': flags})
    hashes = {}
    root = pathlib.Path(__file__).resolve().parents[1]
    for name, expected in protocol['hashes'].items():
        path = pathlib.Path(name) if pathlib.Path(name).is_absolute() else root/name
        if name.startswith('/app/') and args.harness_dir:
            path = args.harness_dir/pathlib.Path(name).name
        # The source extension's relative paths resolve against its separate suite.
        if 'source-extension' in folder.name and not pathlib.Path(name).is_absolute():
            path = root/'cohorts/source-extension'/name
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        hashes[name] = {'match': actual == expected, 'actual': actual, 'frozen': expected}
    result = {'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'complete': len(rows) == len(protocol['jobs']), 'planned_attempts': len(protocol['jobs']),
              'recorded_attempts': len(rows), 'terminal_statuses': dict(collections.Counter(r['record'].get('status') for r in rows)),
              'strict_passes': sum(r['evaluation']['passed'] for r in rows),
              'numeric_agreement_diagnostic': sum(r['evaluation'].get('numeric_pass', False) for r in rows),
              'categories_overlap': True,
              'category_note': 'Mechanistic descriptive labels can overlap. Clarification requests are not automatically proved unnecessary; manual examples distinguish source-specified inputs from genuine method uncertainty. A correct number with a reporting mismatch need not be a mathematical error.',
              'failure_categories': {k: {'count': len(ids), 'example_ids': ids[:2], 'all_ids': ids} for k, ids in sorted(grouped.items())},
              'execution_count': total_executions, 'successful_reviewer_execution_count': successful_review,
              'code_access_flags': code_findings, 'secret_pattern_files': secret_files,
              'leakage_note': 'Regex audit is a screening step, not proof of no leakage. Flagged file/network operations require manual classification; original primary scores are unchanged. Public model training contamination is not observable here.',
              'all_frozen_sources_match': all(v['match'] for v in hashes.values()), 'hashes': hashes}
    if args.harness_dir:
        result['hash_check_note'] = 'Compared prospective image /app hash manifest against archived deployment build-source files; no claim to rerun hash inspection inside an ended cloud process.'
    (folder/'diagnostic-audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['hashes', 'code_access_flags', 'failure_categories']}, indent=2))
    print(json.dumps({k: {'count':v['count'], 'example_ids':v['example_ids']} for k,v in result['failure_categories'].items()}, indent=2))
    print('Flagged code operations:', len(code_findings))


if __name__ == '__main__':
    main()
