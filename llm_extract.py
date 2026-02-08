import json
import os
import sys
import time
import urllib.request
import urllib.error

API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not API_KEY:
    # Try reading from .zshrc
    import re
    with open(os.path.expanduser('~/.zshrc')) as f:
        for line in f:
            m = re.search(r'ANTHROPIC_API_KEY="([^"]+)"', line)
            if m:
                API_KEY = m.group(1)
                break

assert API_KEY, 'No ANTHROPIC_API_KEY found'

TASKS_FILE = 'all_tasks.json'
RAW_DIR = 'results/raw'
OUTPUT_FILE = 'results/agent_results.json'

def load_tasks():
    with open(TASKS_FILE) as f:
        return {t['id']: t for t in json.load(f)}

def get_expected_field(gt):
    ss_fields = ['sample_size_per_group', 'subjects_per_group', 'subjects_per_arm',
                 'sample_size', 'subjects', 'per_cell', 'subjects_per_cluster',
                 'patients_per_cluster', 'total_sample_size', 'total_subjects']
    for f in ss_fields:
        if f in gt and gt[f] is not None:
            return f, gt[f]
    if gt.get('power') is not None:
        # Check if sample size fields are present (then power is NOT the answer)
        has_ss = any(f in gt and gt[f] is not None for f in ss_fields)
        if not has_ss:
            return 'power', gt['power']
    if gt.get('detectable_effect_d') is not None:
        return 'detectable_effect_d', gt['detectable_effect_d']
    # fallback to events
    if gt.get('events_needed') is not None:
        return 'events_needed', gt['events_needed']
    if gt.get('events') is not None:
        return 'events', gt['events']
    return None, None

def call_claude(prompt, max_tokens=200):
    data = json.dumps({
        'model': 'claude-haiku-4-20250414',
        'max_tokens': max_tokens,
        'messages': [{'role': 'user', 'content': prompt}]
    }).encode()
    
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=data,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': API_KEY,
            'anthropic-version': '2023-06-01'
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result['content'][0]['text']
    except urllib.error.HTTPError as e:
        body = e.read().decode() if hasattr(e, 'read') else str(e)
        return f'ERROR: {e.code} {body[:200]}'
    except Exception as e:
        return f'ERROR: {str(e)}'

def extract_number(text):
    """Extract a single number from Claude's response."""
    import re
    text = text.strip()
    # Try direct number
    m = re.match(r'^-?[\d,]+(\.[\d]+)?$', text.replace(',', ''))
    if m:
        return float(text.replace(',', ''))
    # Try "The answer is X"
    m = re.search(r'(?:answer|value|result)\s*(?:is|=|:)\s*(-?[\d,]+(\.[\d]+)?)', text)
    if m:
        return float(m.group(1).replace(',', ''))
    # Try first number in response
    m = re.search(r'(-?[\d,]+(\.[\d]+)?)', text)
    if m:
        return float(m.group(1).replace(',', ''))
    return None

def main():
    tasks = load_tasks()
    results = {}
    log = []
    
    total = len(tasks)
    done = 0
    
    for tid, task in sorted(tasks.items()):
        done += 1
        raw_file = os.path.join(RAW_DIR, f'{tid}.txt')
        if not os.path.exists(raw_file):
            log.append(f'{tid}: MISSING')
            continue
        
        with open(raw_file) as f:
            response_text = f.read()
        
        field, expected = get_expected_field(task.get('ground_truth', {}))
        if field is None:
            log.append(f'{tid}: no expected field in ground truth')
            continue
        
        # Build extraction prompt
        prompt = f"""Extract the single numerical answer from this ChatGPT response to a statistical power analysis question.

The question asked for: {field.replace('_', ' ')}
Expected answer type: {'a decimal between 0 and 1' if field == 'power' else 'an integer (sample size or count)'}

ChatGPT's response:
{response_text[:3000]}

Extract ONLY the final recommended numerical value for {field.replace('_', ' ')}. If the response gives a "per group" number and the field asks for per_group, give the per-group number. If the field asks for total, give the total.

Respond with ONLY the number, nothing else."""
        
        reply = call_claude(prompt)
        value = extract_number(reply)
        
        if value is not None:
            if field == 'power' and value > 1:
                value = value / 100
            results[tid] = value if field == 'power' else int(round(value))
            
            tol_dict = task.get('tolerance', {})
            tol = tol_dict.get('sample_size', tol_dict.get('power', tol_dict.get('subjects', tol_dict.get('clusters', tol_dict.get('effect_size', 10)))))
            diff = abs(results[tid] - expected)
            passed = diff <= tol
            status = 'PASS' if passed else 'FAIL'
            log.append(f'[{done}/{total}] {tid}: extracted={results[tid]}, expected={expected}, diff={diff:.2f}, tol={tol}, {status}')
        else:
            log.append(f'[{done}/{total}] {tid}: EXTRACTION FAILED (Claude said: {reply[:100]})')
        
        # Rate limit
        if done % 10 == 0:
            print(f'  [{done}/{total}] ...', flush=True)
            time.sleep(0.5)
    
    # Write results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    extracted = sum(1 for v in results.values() if v is not None)
    passed = sum(1 for l in log if 'PASS' in l)
    failed = sum(1 for l in log if 'FAIL' in l)
    print(f'\n=== EXTRACTION SUMMARY ===')
    print(f'Extracted: {extracted}/{total}')
    print(f'Passed: {passed}/{total}')
    print(f'Failed: {failed}/{total}')
    print(f'Results: {OUTPUT_FILE}')
    
    # Show failures
    failures = [l for l in log if 'FAIL' in l or 'MISSING' in l or 'EXTRACTION FAILED' in l]
    if failures:
        print(f'\n=== FAILURES ({len(failures)}) ===')
        for fl in failures:
            print(f'  {fl}')

if __name__ == '__main__':
    main()
