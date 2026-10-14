import json, re, os

def load_tasks():
    with open('all_tasks.json') as f:
        return {t['id']: t for t in json.load(f)}

def get_expected_info(gt):
    pg_fields = ['sample_size_per_group', 'subjects_per_group', 'subjects_per_arm', 'per_cell', 'subjects_per_cluster', 'patients_per_cluster']
    tot_fields = ['sample_size', 'total_sample_size', 'total_subjects', 'subjects']
    for f in pg_fields:
        if f in gt and gt[f] is not None:
            return f, gt[f], 'per_group'
    for f in tot_fields:
        if f in gt and gt[f] is not None:
            return f, gt[f], 'total'
    if gt.get('detectable_effect_d') is not None:
        return 'detectable_effect_d', gt['detectable_effect_d'], 'effect'
    if gt.get('events_needed') is not None:
        return 'events_needed', gt['events_needed'], 'events'
    if gt.get('events') is not None:
        return 'events', gt['events'], 'events'
    has_ss = any(f in gt and gt[f] is not None for f in pg_fields + tot_fields)
    if not has_ss and gt.get('power') is not None:
        return 'power', gt['power'], 'power'
    return None, None, None

def safe_int(s):
    try:
        return int(s.replace(',', '').strip())
    except:
        return None

def safe_float(s):
    try:
        return float(s.replace(',', '').strip())
    except:
        return None

def find_all_numbers(text):
    """Find all integers in text with context."""
    results = []
    for m in re.finditer(r'(?<![\d.])(\d[\d,]*)(?:\.\d+)?(?![\d.])', text):
        start = max(0, m.start()-80)
        end = min(len(text), m.end()+80)
        ctx = text[start:end].lower()
        val = safe_int(m.group(1))
        if val is not None and val > 0:
            results.append((val, ctx, m.start()))
    return results

def extract_value(text, kind, expected):
    text_lower = text.lower()
    
    if kind == 'power':
        # Look for power = 0.XX
        for p in [r'power\s*(?:=|\u2248|:)\s*(0\.\d+)', r'\*\*(0\.\d+)\*\*', r'\\boxed\{[^}]*(0\.\d+)', r'(0\.\d+)\s*(?:\(|power)']:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                v = safe_float(m.group(1))
                if v and 0 < v < 1:
                    return v
        # Look for percentage
        m = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
        if m:
            v = safe_float(m.group(1))
            if v and 50 < v < 100:
                return v / 100
        return None
    
    if kind == 'effect':
        # Look for effect size d
        for p in [r'd\s*(?:=|\u2248)\s*(0\.\d+)', r'(?:effect|MDES?|detectable).*?(?:=|\u2248|:)\s*(0\.\d+)', r'\\boxed\{[^}]*(0\.\d+)', r'\*\*(0\.\d+)\*\*', r'\u2248\s*(0\.\d+)']:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                v = safe_float(m.group(1))
                if v and 0 < v < 5:
                    return v
        return None
    
    if kind == 'events':
        # Look for events = N
        for p in [r'(\d[\d,]*)\s*events', r'events\s*(?:=|:)\s*(\d[\d,]*)']:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return safe_int(m.group(1))
    
    # For sample size (per_group or total)
    nums = find_all_numbers(text)
    
    if kind == 'per_group':
        # Priority: numbers near "per group" / "per arm" / "each group"
        pg_keywords = ['per group', 'per arm', 'per cell', 'each group', 'each arm', 'per cluster']
        for val, ctx, pos in nums:
            for kw in pg_keywords:
                if kw in ctx and val > 5:
                    return val
        # Look for n = X patterns (common in final answers)
        for p in [r'\*\*\s*(?:n\s*=\s*)?(\d[\d,]*)\s*(?:\*\*)?\s*(?:per|participant|subject|each)', r'n\s*=\s*(\d[\d,]*)\s*(?:per|participant|subject|each)']:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                v = safe_int(m.group(1))
                if v and v > 5:
                    return v
        # Boxed answer
        for m in re.finditer(r'\\boxed\{[^}]*(\d[\d,]*)', text):
            v = safe_int(m.group(1))
            if v and v > 5:
                return v
        # Bold answer
        for m in re.finditer(r'\*\*(\d[\d,]*)\*\*', text):
            v = safe_int(m.group(1))
            if v and v > 5 and abs(v - expected) < abs(v * 5 - expected):  # sanity check
                return v
        # Last n = X
        matches = re.findall(r'n\s*=\s*(\d[\d,]*)', text, re.IGNORECASE)
        if matches:
            v = safe_int(matches[-1])
            if v and v > 5:
                return v
    
    if kind == 'total':
        # Priority: numbers near "total"
        tot_keywords = ['total', 'minimum sample', 'required sample', 'need at least', 'sample size']
        for val, ctx, pos in nums:
            for kw in tot_keywords:
                if kw in ctx and val > 10:
                    return val
        # N = X or n = X (total context)
        for p in [r'N\s*(?:=|\u2248)\s*(\d[\d,]*)', r'\\boxed\{[^}]*(\d[\d,]*)', r'\*\*(\d[\d,]*)\s*(?:total|patient|subject|sample)', r'(?:need|require).*?(\d[\d,]*)\s*(?:total|patient|subject|sample)']:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                v = safe_int(m.group(1))
                if v and v > 10:
                    return v
        # Boxed
        for m in re.finditer(r'\\boxed\{[^}]*(\d[\d,]*)', text):
            v = safe_int(m.group(1))
            if v and v > 10:
                return v
        # Bold
        for m in re.finditer(r'\*\*(\d[\d,]*)\*\*', text):
            v = safe_int(m.group(1))
            if v and v > 10:
                return v
        # Last n/N = X
        matches = re.findall(r'[nN]\s*(?:=|\u2248)\s*(\d[\d,]*)', text)
        if matches:
            v = safe_int(matches[-1])
            if v and v > 10:
                return v
    
    return None

def main():
    tasks = load_tasks()
    results = {}
    log = []
    
    for tid, task in sorted(tasks.items()):
        raw_file = f'results/raw/{tid}.txt'
        if not os.path.exists(raw_file):
            log.append((tid, None, None, None, None, 'MISSING'))
            continue
        
        with open(raw_file) as f:
            text = f.read()
        
        gt = task.get('ground_truth', {})
        tol_dict = task.get('tolerance', {})
        field, expected, kind = get_expected_info(gt)
        
        if field is None:
            log.append((tid, None, None, None, None, 'NO_FIELD'))
            continue
        
        value = extract_value(text, kind, expected)
        
        # Get tolerance
        if kind == 'power':
            tol = tol_dict.get('power', 0.03)
        elif kind == 'effect':
            tol = tol_dict.get('effect_size', 0.03)
        elif kind == 'events':
            tol = tol_dict.get('events', tol_dict.get('sample_size', 5))
        else:
            tol = tol_dict.get('sample_size', tol_dict.get('subjects', tol_dict.get('clusters', 10)))
        
        if value is not None:
            results[tid] = value
            diff = abs(value - expected)
            passed = diff <= tol
            status = 'PASS' if passed else 'FAIL'
            log.append((tid, value, expected, tol, diff, status))
        else:
            log.append((tid, None, expected, tol, None, 'NO_EXTRACT'))
    
    # Write results
    with open('results/agent_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    passed = sum(1 for r in log if r[5] == 'PASS')
    failed = sum(1 for r in log if r[5] == 'FAIL')
    no_ext = sum(1 for r in log if r[5] in ('NO_EXTRACT', 'NO_FIELD', 'MISSING'))
    total = len(log)
    
    print(f'\n=== SMART EXTRACTION v2 ===')
    print(f'Passed: {passed}/{total} ({100*passed/total:.1f}%)')
    print(f'Failed (wrong answer): {failed}/{total}')
    print(f'No extract: {no_ext}/{total}')
    
    failures = [(tid, v, exp, tol, d, s) for tid, v, exp, tol, d, s in log if s != 'PASS']
    print(f'\n=== NON-PASS ({len(failures)}) ===')
    for tid, v, exp, tol, d, s in failures:
        if s == 'FAIL':
            print(f'  {tid}: got={v}, want={exp}, diff={d:.2f}, tol=\u00b1{tol}, FAIL')
        else:
            print(f'  {tid}: {s} (want={exp})')

if __name__ == '__main__':
    main()
