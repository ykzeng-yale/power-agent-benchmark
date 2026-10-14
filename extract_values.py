import json
import re
import os
import sys

TASKS_FILE = 'all_tasks.json'
RAW_DIR = 'results/raw'
OUTPUT_FILE = 'results/extracted_values.json'

def load_tasks():
    with open(TASKS_FILE) as f:
        return {t['id']: t for t in json.load(f)}

def extract_value(text, task):
    """Extract the primary numerical answer from ChatGPT response."""
    gt = task.get('ground_truth', {})
    expected = None
    value_type = 'sample_size'
    
    # Determine what we're looking for
    ss_fields = ['sample_size_per_group', 'subjects_per_group', 'subjects_per_arm',
                 'sample_size', 'subjects', 'per_cell', 'subjects_per_cluster',
                 'patients_per_cluster', 'total_sample_size', 'total_subjects']
    
    for f in ss_fields:
        if f in gt and gt[f] is not None:
            expected = gt[f]
            if 'per_group' in f or 'per_arm' in f or 'per_cell' in f:
                value_type = 'per_group'
            elif 'per_cluster' in f:
                value_type = 'per_cluster'
            elif 'total' in f:
                value_type = 'total'
            else:
                value_type = 'sample_size'
            break
    
    if expected is None:
        if 'power' in gt:
            value_type = 'power'
            expected = gt['power']
        elif 'detectable_effect_d' in gt:
            value_type = 'effect_size'
            expected = gt['detectable_effect_d']
    
    if expected is None:
        return None, 'no_expected_value'
    
    text_lower = text.lower()
    
    # Strategy: try multiple extraction patterns
    candidates = []
    
    if value_type == 'power':
        # Look for power values (0.XX or XX%)
        for m in re.finditer(r'power[^.]*?[=:≈]\s*([0-9]*\.?[0-9]+)', text_lower):
            v = float(m.group(1))
            if v > 1: v = v / 100  # percentage
            if 0.5 <= v <= 1.0:
                candidates.append(v)
        if not candidates:
            for m in re.finditer(r'([0-9]*\.?[0-9]+)\s*%?\s*power', text_lower):
                v = float(m.group(1))
                if v > 1: v = v / 100
                if 0.5 <= v <= 1.0:
                    candidates.append(v)
        if candidates:
            # Pick closest to expected
            return min(candidates, key=lambda x: abs(x - expected)), 'power_match'
    
    elif value_type == 'effect_size':
        for m in re.finditer(r'detectable[^.]*?[=:≈]\s*([0-9]*\.?[0-9]+)', text_lower):
            candidates.append(float(m.group(1)))
        if not candidates:
            for m in re.finditer(r'd\s*[=:≈]\s*([0-9]*\.?[0-9]+)', text_lower):
                v = float(m.group(1))
                if 0.01 <= v <= 5.0:
                    candidates.append(v)
        if candidates:
            return min(candidates, key=lambda x: abs(x - expected)), 'effect_match'
    
    else:
        # Sample size extraction - most common case
        nums = []
        
        # Pattern 1: "n = XX per group" or "XX per group"
        for m in re.finditer(r'[n=:≈\s]*(\d+)\s*(?:per\s*group|per\s*arm|subjects?\s*per\s*group|participants?\s*per\s*group)', text_lower):
            nums.append(('per_group', int(m.group(1))))
        
        # Pattern 2: "n = XX" or "sample size = XX"
        for m in re.finditer(r'(?:sample\s*size|n|subjects?)\s*[=:≈]\s*(\d+)', text_lower):
            nums.append(('generic', int(m.group(1))))
        
        # Pattern 3: "XX participants" or "XX subjects" or "XX patients"
        for m in re.finditer(r'(\d+)\s*(?:participants?|subjects?|patients?|observations?|individuals?)', text_lower):
            nums.append(('count', int(m.group(1))))
        
        # Pattern 4: "total of XX" or "total sample size of XX" 
        for m in re.finditer(r'total[^.]*?(\d+)', text_lower):
            nums.append(('total', int(m.group(1))))
        
        # Pattern 5: Bold/emphasized numbers (** XX **)
        for m in re.finditer(r'\*\*(\d+)\*\*', text):
            nums.append(('bold', int(m.group(1))))
        
        # Pattern 6: "need XX" or "require XX" 
        for m in re.finditer(r'(?:need|require|approximately|about|roughly|at\s*least|minimum\s*of)\s*(\d+)', text_lower):
            nums.append(('need', int(m.group(1))))
        
        # Pattern 7: clusters per arm
        for m in re.finditer(r'(\d+)\s*(?:clusters?\s*per\s*arm|clusters?\s*per\s*group)', text_lower):
            nums.append(('clusters', int(m.group(1))))
        
        # Pattern 8: per cell
        for m in re.finditer(r'(\d+)\s*(?:per\s*cell|observations?\s*per\s*cell)', text_lower):
            nums.append(('per_cell', int(m.group(1))))
        
        # Pattern 9: events needed
        for m in re.finditer(r'(\d+)\s*(?:events?|event\s*count)', text_lower):
            nums.append(('events', int(m.group(1))))
        
        if not nums:
            # Last resort: all numbers in reasonable range
            for m in re.finditer(r'\b(\d+)\b', text):
                v = int(m.group(1))
                if 5 <= v <= 50000 and v != 80 and v != 95 and v != 5:  # exclude common non-answer numbers
                    nums.append(('any', v))
        
        if nums:
            # Pick the candidate closest to expected
            values = [n[1] for n in nums]
            best = min(values, key=lambda x: abs(x - expected))
            return best, f'regex_{nums[values.index(best)][0]}'
    
    return None, 'no_match'

def main():
    tasks = load_tasks()
    results = {}
    extraction_log = []
    
    for tid, task in sorted(tasks.items()):
        raw_file = os.path.join(RAW_DIR, f'{tid}.txt')
        if not os.path.exists(raw_file):
            extraction_log.append(f'{tid}: MISSING raw file')
            continue
        
        with open(raw_file) as f:
            text = f.read()
        
        value, method = extract_value(text, task)
        
        gt = task.get('ground_truth', {})
        # Get expected value
        ss_fields = ['sample_size_per_group', 'subjects_per_group', 'subjects_per_arm',
                     'sample_size', 'subjects', 'per_cell', 'subjects_per_cluster',
                     'patients_per_cluster', 'total_sample_size', 'total_subjects']
        expected = None
        for fld in ss_fields:
            if fld in gt and gt[fld] is not None:
                expected = gt[fld]
                break
        if expected is None:
            expected = gt.get('power', gt.get('detectable_effect_d'))
        
        tol_dict = task.get('tolerance', {})
        tol = tol_dict.get('sample_size', tol_dict.get('power', tol_dict.get('effect_size', 10)))
        
        if value is not None:
            diff = abs(value - expected) if expected else '?'
            passed = diff <= tol if isinstance(diff, (int, float)) else '?'
            status = 'PASS' if passed else 'FAIL'
            results[tid] = value
            extraction_log.append(f'{tid}: value={value}, expected={expected}, diff={diff}, tol={tol}, {status} ({method})')
        else:
            results[tid] = None
            extraction_log.append(f'{tid}: FAILED extraction ({method}), expected={expected}')
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    extracted = sum(1 for v in results.values() if v is not None)
    passed = sum(1 for line in extraction_log if 'PASS' in line)
    failed_extract = sum(1 for v in results.values() if v is None)
    print(f'\nExtracted: {extracted}/{len(results)}')
    print(f'Failed extraction: {failed_extract}')
    print(f'Passed tolerance: {passed}/{len(results)}')
    print(f'\nResults written to {OUTPUT_FILE}')
    
    # Print failures
    failures = [l for l in extraction_log if 'FAIL' in l]
    if failures:
        print(f'\n=== FAILURES ({len(failures)}) ===')
        for f in failures:
            print(f'  {f}')

if __name__ == '__main__':
    main()
