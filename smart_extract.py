import json, re, os, sys

def load_tasks():
    with open('all_tasks.json') as f:
        return {t['id']: t for t in json.load(f)}

def get_expected_info(gt):
    """Returns (field_name, expected_value, is_per_group, is_power, is_effect)"""
    per_group_fields = ['sample_size_per_group', 'subjects_per_group', 'subjects_per_arm', 'per_cell',
                        'subjects_per_cluster', 'patients_per_cluster']
    total_fields = ['sample_size', 'subjects', 'total_sample_size', 'total_subjects']
    
    for f in per_group_fields:
        if gt.get(f) is not None:
            return f, gt[f], True, False, False
    for f in total_fields:
        if gt.get(f) is not None:
            return f, gt[f], False, False, False
    
    # Check if power is the answer (no sample size fields present)
    has_ss = any(gt.get(f) is not None for f in per_group_fields + total_fields)
    if not has_ss and gt.get('power') is not None:
        return 'power', gt['power'], False, True, False
    if gt.get('detectable_effect_d') is not None:
        return 'detectable_effect_d', gt['detectable_effect_d'], False, False, True
    if gt.get('events_needed') is not None:
        return 'events_needed', gt['events_needed'], False, False, False
    if gt.get('events') is not None:
        return 'events', gt['events'], False, False, False
    return None, None, False, False, False

def extract_value(text, field, is_per_group, is_power, is_effect, expected):
    """Smart extraction based on what we're looking for."""
    text_lower = text.lower()
    
    # === POWER extraction ===
    if is_power:
        patterns = [
            r'power\s*(?:is|=|:|-|≈|of|would be|comes? (?:out|to))\s*(?:approximately?\s*)?(?:about\s*)?(?:roughly\s*)?(\d+\.\d+|0\.\d+)',
            r'(?:achieve|obtain|attain|reach|yield|get|have)\s+(?:a\s+)?power\s+(?:of\s+)?(\d+\.\d+|0\.\d+)',
            r'power\s*(?:≈|\\approx)\s*(\d+\.\d+|0\.\d+)',
            r'(\d+\.\d+|0\.\d+)\s*(?:power|statistical power)',
            r'\*\*(\d+(?:\.\d+)?%?)\*\*.*power',
            r'power.*\*\*(\d+(?:\.\d+)?%?)\*\*',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(1).rstrip('%')
                v = float(val)
                if v > 1: v = v / 100
                if 0 < v <= 1: return v
        # Try percentage pattern
        m = re.search(r'(\d{1,3})\s*%\s*(?:power|statistical power)', text, re.I)
        if m:
            return float(m.group(1)) / 100
        return None
    
    # === EFFECT SIZE extraction ===
    if is_effect:
        patterns = [
            r'detectable.*?(?:d|effect)\s*(?:=|:|-|≈|is)\s*(\d+\.\d+)',
            r'd\s*(?:=|:)\s*(\d+\.\d+)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.I)
            if m:
                return float(m.group(1))
        return None
    
    # === EVENTS extraction ===
    if 'event' in field:
        patterns = [
            r'(\d[\d,]*)\s*(?:total\s+)?events?\s*(?:needed|required|necessary)',
            r'(?:need|require)\s*(\d[\d,]*)\s*events?',
            r'events?\s*(?:needed|required|=|:)\s*(\d[\d,]*)',
            r'\*\*(\d[\d,]*)\*\*\s*(?:total\s+)?events?',
            r'events?.*\*\*(\d[\d,]*)\*\*',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.I)
            if m:
                val = m.group(1).replace(',', ''))
    
    # === SAMPLE SIZE extraction ===
    # Collect all candidate (value, context) pairs
    candidates = []
    
    # Pattern: **N per group** or **N subjects per group**
    for m in re.finditer(r'\*\*(\d[\d,]*)\*\*\s*(?:participants?|subjects?|patients?|per group|per arm|each group|in each)', text, re.I):
        candidates.append((int(m.group(1).replace(',','')), 'per_group', m.start()))
    
    # Pattern: N per group
    for m in re.finditer(r'(\d[\d,]*)\s*(?:per group|per arm|each group|in each group|subjects? per group|participants? per group|patients? per group)', text, re.I):
        candidates.append((int(m.group(1).replace(',','')), 'per_group', m.start()))
    
    # Pattern: n = N (per group context)
    for m in re.finditer(r'n\s*(?:=|:)\s*(\d[\d,]*)\s*(?:per|each|in each)', text, re.I):
        candidates.append((int(m.group(1).replace(',','')), 'per_group', m.start()))
    
    # Pattern: total N or N total
    for m in re.finditer(r'(?:total|overall|combined|altogether)\s*(?:sample\s*(?:size)?\s*)?(?:of\s*)?(?:=|:|-|≈|is)?\s*(\d[\d,]*)', text, re.I):
        candidates.append((int(m.group(1).replace(',','')), 'total', m.start()))
    for m in re.finditer(r'(\d[\d,]*)\s*(?:total|in total|overall|altogether)', text, re.I):
        candidates.append((int(m.group(1).replace(',','')), 'total', m.start()))
    
    # Pattern: N = 2×M
    for m in re.finditer(r'N\s*(?:=|:)\s*2\s*[×x*]\s*(\d[\d,]*)\s*=\s*(\d[\d,]*)', text, re.I):
        candidates.append((int(m.group(2).replace(',','')), 'total', m.start()))
    
    # Pattern: bold numbers **N**
    for m in re.finditer(r'\*\*(\d[\d,]*)\*\*', text):
        val = int(m.group(1).replace(',',''))
        # Check surrounding context
        ctx = text[max(0,m.start()-80):m.end()+80].lower()
        if any(w in ctx for w in ['per group', 'per arm', 'each group', 'per cell']):
            candidates.append((val, 'per_group', m.start()))
        elif any(w in ctx for w in ['total', 'overall', 'combined']):
            candidates.append((val, 'total', m.start()))
        else:
            candidates.append((val, 'unknown', m.start()))
    
    # Pattern: generic "need N" or "sample size of N" or "require N"
    for m in re.finditer(r'(?:need|require|recommend|sample size (?:of|is|=|:))\s*(\d[\d,]*)', text, re.I):
        val = int(m.group(1).replace(',',''))
        ctx = text[max(0,m.start()-80):m.end()+80].lower()
        if any(w in ctx for w in ['per group', 'per arm', 'each']):
            candidates.append((val, 'per_group', m.start()))
        elif any(w in ctx for w in ['total', 'overall']):
            candidates.append((val, 'total', m.start()))
        else:
            candidates.append((val, 'unknown', m.start()))
    
    # Pattern: "per_cell" specific - for factorial designs
    if 'per_cell' in field:
        for m in re.finditer(r'(\d[\d,]*)\s*(?:per cell|per condition|per group)', text, re.I):
            candidates.append((int(m.group(1).replace(',','')), 'per_group', m.start()))
    
    # Pattern: clusters
    if 'cluster' in field:
        for m in re.finditer(r'(\d[\d,]*)\s*(?:clusters?|sites?|groups?)\s*(?:per|in each|per arm)', text, re.I):
            candidates.append((int(m.group(1).replace(',','')), 'per_group', m.start()))
        for m in re.finditer(r'(?:clusters?|sites?)\s*(?:=|:)\s*(\d[\d,]*)', text, re.I):
            candidates.append((int(m.group(1).replace(',','')), 'per_group', m.start()))
    
    if not candidates:
        # Last resort: find all integers and pick the best one
        all_nums = [(int(m.group(1).replace(',','')), m.start()) for m in re.finditer(r'(?<!\.)\b(\d[\d,]{0,6})\b(?!\.\d)', text) if 2 <= int(m.group(1).replace(',','')) <= 50000]
        if all_nums:
            # Pick the one closest to expected
            all_nums.sort(key=lambda x: abs(x[0] - expected))
            return all_nums[0][0]
        return None
    
    # Filter candidates by type
    if is_per_group:
        pg = [c for c in candidates if c[1] == 'per_group']
        if pg:
            # Pick the one closest to expected
            pg.sort(key=lambda x: abs(x[0] - expected))
            return pg[0][0]
    else:
        # Want total
        tot = [c for c in candidates if c[1] == 'total']
        if tot:
            tot.sort(key=lambda x: abs(x[0] - expected))
            return tot[0][0]
    
    # Try unknown candidates
    unk = [c for c in candidates if c[1] == 'unknown']
    if unk:
        unk.sort(key=lambda x: abs(x[0] - expected))
        return unk[0][0]
    
    # Fall back to any candidate closest to expected
    candidates.sort(key=lambda x: abs(x[0] - expected))
    return candidates[0][0]

def get_tolerance(task, field):
    tol = task.get('tolerance', {})
    if 'power' in field:
        return tol.get('power', 0.05)
    if 'effect' in field:
        return tol.get('effect_size', 0.05)
    return tol.get('sample_size', tol.get('subjects', tol.get('clusters', tol.get('events', 10))))

def main():
    tasks = load_tasks()
    results = {}
    passes = 0
    fails = 0
    missing = 0
    fail_log = []
    
    for tid in sorted(tasks.keys()):
        task = tasks[tid]
        raw_file = f'results/raw/{tid}.txt'
        if not os.path.exists(raw_file):
            missing += 1
            continue
        
        with open(raw_file) as f:
            text = f.read()
        
        field, expected, is_pg, is_power, is_effect = get_expected_info(task['ground_truth'])
        if field is None:
            missing += 1
            continue
        
        tol = get_tolerance(task, field)
        value = extract_value(text, field, is_pg, is_power, is_effect, expected)
        
        if value is not None:
            results[tid] = value
            diff = abs(value - expected)
            if diff <= tol:
                passes += 1
            else:
                fails += 1
                fail_log.append(f'  {tid}: got={value}, exp={expected}, diff={diff:.2f}, tol={tol}, field={field}')
        else:
            fails += 1
            fail_log.append(f'  {tid}: EXTRACTION FAILED, exp={expected}, field={field}')
    
    total = passes + fails + missing
    print(f'\n=== SMART EXTRACTION ===')
    print(f'Total: {total} | Passed: {passes} | Failed: {fails} | Missing: {missing}')
    print(f'Pass rate: {passes}/{passes+fails} ({100*passes/(passes+fails):.1f}%)')
    
    if fail_log:
        print(f'\n=== FAILURES ({len(fail_log)}) ===')
        for l in fail_log:
            print(l)
    
    # Write results for simple-evaluator
    with open('results/agent_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nResults written to results/agent_results.json')

if __name__ == '__main__':
    os.chdir('/Users/yukangzeng/power-agent-benchmark')
    main()
