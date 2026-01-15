#!/usr/bin/env python
"""
Measure OCR Accuracy against Ground Truth
"""
import json
import argparse
from pathlib import Path
from difflib import SequenceMatcher

def normalize_text(text):
    """Normalize text for fuzzy comparison"""
    if text is None:
        return ""
    if isinstance(text, bool):
        return str(text).lower()
    return str(text).lower().strip().replace('\n', ' ')

def calculate_cer(reference, hypothesis):
    """Calculate Character Error Rate"""
    ref = normalize_text(reference)
    hyp = normalize_text(hypothesis)
    
    if not ref and not hyp:
        return 0.0
    if not ref:
        return 1.0
        
    # Levenshtein distance
    m = SequenceMatcher(None, ref, hyp)
    distance = 1 - m.ratio()
    return distance

def flatten_json(y):
    """Flatten nested dictionary"""
    out = {}
    
    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            for i, a in enumerate(x):
                flatten(a, name + str(i) + '_')
        else:
            out[name[:-1]] = x
            
    flatten(y)
    return out

def evaluate_page(page_num, pred_page, truth_page):
    """Evaluate a single page"""
    metrics = {
        'total_fields': 0,
        'exact_matches': 0,
        'norm_matches': 0,
        'cer_sum': 0
    }
    
    # Extract all relevant data fields
    pred_data = {**pred_page.get('form_fields', {}), **pred_page.get('signatures', {}), **pred_page.get('part_b', {}), **pred_page.get('third_party_payment_form', {})}
    truth_data = {**truth_page.get('form_fields', {}), **truth_page.get('signatures', {}), **truth_page.get('part_b', {}), **truth_page.get('third_party_payment_form', {})}
    
    # Flatten strictly for comparisons
    pred_flat = flatten_json(pred_data)
    truth_flat = flatten_json(truth_data)
    
    for key, truth_val in truth_flat.items():
        if truth_val is None: 
            # Skip checking nulls for now unless we want to enforce null detection
            continue
            
        metrics['total_fields'] += 1
        pred_val = pred_flat.get(key)
        
        # Exact Match
        if pred_val == truth_val:
            metrics['exact_matches'] += 1
            
        # Normalized Match
        norm_ref = normalize_text(truth_val)
        norm_hyp = normalize_text(pred_val)
        
        if norm_ref == norm_hyp:
            metrics['norm_matches'] += 1
            
        # CER
        cer = calculate_cer(truth_val, pred_val)
        metrics['cer_sum'] += cer
        
    return metrics

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pred', required=True, help='Prediction JSON file')
    parser.add_argument('--truth', required=True, help='Ground Truth JSON file')
    args = parser.parse_args()
    
    import sys
    
    # Force UTF-8 for stdout/stderr to avoid Windows console errors
    sys.stdout.reconfigure(encoding='utf-8')

    with open(args.pred, 'r', encoding='utf-8') as f:
        pred_json = json.load(f)
        
    with open(args.truth, 'r', encoding='utf-8') as f:
        truth_json = json.load(f)
        
    # Output file
    with open('final_accuracy.txt', 'w', encoding='utf-8') as outfile:
        def log(msg):
            print(msg)
            outfile.write(msg + '\n')

        log(f"Comparing {Path(args.pred).name} vs {Path(args.truth).name}")
        log("="*80)
        log(f"{'Page':<10} | {'Total Fields':<12} | {'Exact Match':<12} | {'Norm Match':<12} | {'Avg CER':<10}")
        log("-" * 80)
        
        total_metrics = {'total_fields': 0, 'exact_matches': 0, 'norm_matches': 0, 'cer_sum': 0}
        
        # Iterate through ground truth pages
        for i, truth_page in enumerate(truth_json['pages']):
            page_num = truth_page['page']
            
            # Find corresponding prediction page
            pred_page = next((p for p in pred_json['pages'] if p['page'] == page_num), {})
            
            metrics = evaluate_page(page_num, pred_page, truth_page)
            
            # Aggregate
            for k in total_metrics:
                total_metrics[k] += metrics[k]
                
            avg_cer = metrics['cer_sum'] / metrics['total_fields'] if metrics['total_fields'] > 0 else 0
            exact_acc = (metrics['exact_matches'] / metrics['total_fields'] * 100) if metrics['total_fields'] > 0 else 0
            norm_acc = (metrics['norm_matches'] / metrics['total_fields'] * 100) if metrics['total_fields'] > 0 else 0
            
            log(f"{page_num:<10} | {metrics['total_fields']:<12} | {exact_acc:6.1f}%      | {norm_acc:6.1f}%      | {avg_cer:.4f}")

        log("-" * 80)
        
        # Grand Total
        t_avg_cer = total_metrics['cer_sum'] / total_metrics['total_fields'] if total_metrics['total_fields'] > 0 else 0
        t_exact_acc = (total_metrics['exact_matches'] / total_metrics['total_fields'] * 100) if total_metrics['total_fields'] > 0 else 0
        t_norm_acc = (total_metrics['norm_matches'] / total_metrics['total_fields'] * 100) if total_metrics['total_fields'] > 0 else 0
        
        log(f"{'TOTAL':<10} | {total_metrics['total_fields']:<12} | {t_exact_acc:6.1f}%      | {t_norm_acc:6.1f}%      | {t_avg_cer:.4f}")
        log("=" * 80)

        # Mismatch Breakdown
        log("\nMISMATCH DETAILS:")
        for i, truth_page in enumerate(truth_json['pages']):
            page_num = truth_page['page']
            pred_page = next((p for p in pred_json['pages'] if p['page'] == page_num), {})
            
            pred_data = {**pred_page.get('form_fields', {}), **pred_page.get('signatures', {}), **pred_page.get('part_b', {}), **pred_page.get('tables', {}), **pred_page.get('third_party_payment_form', {})}
            truth_data = {**truth_page.get('form_fields', {}), **truth_page.get('signatures', {}), **truth_page.get('part_b', {}), **truth_page.get('tables', {}), **truth_page.get('third_party_payment_form', {})}
            
            pred_flat = flatten_json(pred_data)
            truth_flat = flatten_json(truth_data)
            
            for key, truth_val in truth_flat.items():
                if truth_val is None: continue
                pred_val = pred_flat.get(key)
                norm_ref = normalize_text(truth_val)
                norm_hyp = normalize_text(pred_val)
                
                if norm_ref != norm_hyp:
                    log(f"[Page {page_num}] Field '{key}': Expected '{truth_val}' / Got '{pred_val}'")

if __name__ == '__main__':
    main()
