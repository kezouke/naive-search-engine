#!/usr/bin/env python3
import sys
import traceback


def tokenize(text):
    # Naive tokenizer: split on whitespace
    return text.lower().split()


try:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        # We expect a TSV line: doc_id \t doc_title \t doc_text
        parts = line.split("\t", 2)
        if len(parts) != 3:
            # Print a debug message to stderr for invalid format
            sys.stderr.write(f"[mapper1] Skipping line (unexpected format): {line}\n")
            continue

        doc_id, doc_title, doc_text = parts
        tokens = tokenize(doc_text)
        doc_length = len(tokens)

        # Output one line to stdout for each document
        # Format: DOC \t doc_id \t doc_title \t doc_length
        print(f"DOC\t{doc_id}\t{doc_title}\t{doc_length}")

except Exception as e:
    # Print the error details to stderr, so Hadoop can log it
    sys.stderr.write(f"[mapper1] Error: {str(e)}\n")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
