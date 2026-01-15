#!/usr/bin/env python
"""Quick verification script to show extracted form data"""
import json
from pathlib import Path

# Find the latest form JSON
output_dir = Path('data/output/json')
form_jsons = list(output_dir.glob('*_form.json'))

if not form_jsons:
    print("No form JSON files found!")
    exit(1)

# Get the latest
latest = sorted(form_jsons)[-1]
print(f"Loading: {latest.name}\n")

with open(latest) as f:
    data = json.load(f)

# Print document info
doc = data['document']
print("=" * 60)
print("DOCUMENT INFORMATION")
print("=" * 60)
print(f"Type: {doc.get('document_type')}")
print(f"Total Pages: {doc.get('total_pages')}")
print(f"DocuSign ID: {doc.get('docu_sign_envelope_id')}")
print(f"Extracted: {doc.get('extracted_at')}\n")

# Print page 1 data
if len(data['pages']) > 0:
    print("=" * 60)
    print("PAGE 1: CLAIMANT INFORMATION")
    print("=" * 60)
    p1_fields = data['pages'][0].get('form_fields', {})
    for key, value in p1_fields.items():
        if value:
            print(f"  {key}: {value}")

# Print page 3 data
if len(data['pages']) > 2:
    print("\n" + "=" * 60)
    print("PAGE 3: MEDICAL INFORMATION")
    print("=" * 60)
    p3_fields = data['pages'][2].get('form_fields', {})
    for key, value in p3_fields.items():
        if value:
            print(f"  {key}: {value}")

# Print page 4 signatures
if len(data['pages']) > 3:
    print("\n" + "=" * 60)
    print("PAGE 4: SIGNATURES")
    print("=" * 60)
    sigs = data['pages'][3].get('signatures', {})
    for key, value in sigs.items():
        if value:
            print(f"  {key}: {value}")

# Print page 5 supplements
if len(data['pages']) > 4:
    print("\n" + "=" * 60)
    print("PAGE 5: MEDICAL CHARGES (SUPPLEMENT A)")
    print("=" * 60)
    tables = data['pages'][4].get('tables', {})
    items = tables.get('supplement_a_items', [])
    if items:
        for i, item in enumerate(items, 1):
            print(f"\n  Item {i}:")
            for key, value in item.items():
                if value:
                    print(f"    {key}: {value}")
    else:
        print("  No items found")

print("\n" + "=" * 60)
print(f"✅ Successfully extracted data from {latest.name}")
print("=" * 60)
