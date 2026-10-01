#!/usr/bin/env node
// Legacy ground-truth-to-LLM judging and success-selecting retries are retired.
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const script=path.join(path.dirname(fileURLToPath(import.meta.url)),'audited_benchmark_v2_0_2.py');
if(process.argv.slice(2).some(a=>a.startsWith('--tier')||a==='--legacy')){
  process.stderr.write('Legacy 106-task scoring is quarantined. Use the audited suite with --cli or --endpoint, --split, --repeats, and a fresh --out directory. See README.md.\n');process.exit(2);
}
const child=spawn(process.env.POWER_AGENT_BENCHMARK_PYTHON||'python3',[script,...process.argv.slice(2)],{stdio:'inherit'});
child.on('error',e=>{process.stderr.write(e.message+'\n');process.exitCode=1});child.on('close',code=>{process.exitCode=code??1});
