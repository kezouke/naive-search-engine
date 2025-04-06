#!/usr/bin/env python3
import sys
from collections import defaultdict

def tokenize(text):
    return text.lower().split()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split("\t", 2)
    if len(parts) != 3:
        continue
    doc_id, doc_title, doc_text = parts
    tokens = tokenize(doc_text)

    # Partial counting in the mapper
    term_counts = defaultdict(int)
    for t in tokens:
        term_counts[t] += 1

    # Emit <term> <tab> <doc_id> <tab> <tf>
    for term, tf in term_counts.items():
        print(f"{term}\t{doc_id}\t{tf}")
