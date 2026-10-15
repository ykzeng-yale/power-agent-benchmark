#!/usr/bin/env python3
"""Print an answer-free development request; this is not a frozen experiment."""
import argparse
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audited', ROOT/'runner/audited_benchmark.py')
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)
parser = argparse.ArgumentParser()
parser.add_argument('task_id')
parser.add_argument('--mode', choices=['single', 'multi'], default='single')
args = parser.parse_args()
tasks = json.loads((ROOT/'audited/tasks.json').read_text())['tasks']
task = next((t for t in tasks if t['id'] == args.task_id), None)
if task is None:
    parser.error('Unknown audited task ID')
print(json.dumps(benchmark.public_request(task, args.mode)))
