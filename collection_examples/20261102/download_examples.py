#!/usr/bin/env python3
"""Download the seven public source PDFs and verify their recorded bytes (CPU only)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true', help='Check existing PDFs without network access.')
    parser.add_argument('--ids', nargs='+', help='Optional source_id subset from sources.json.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    records = json.loads((root / 'sources.json').read_text(encoding='utf-8'))
    known = {r['source_id'] for r in records}
    if args.ids and set(args.ids) - known:
        parser.error('Unknown source_id: ' + ', '.join(sorted(set(args.ids) - known)))
    for record in records:
        if args.ids and record['source_id'] not in args.ids:
            continue
        path = root / record['local_pdf']
        if not path.exists():
            if args.verify_only:
                raise SystemExit('Missing PDF: ' + str(path))
            print('Downloading', record['source_id'], '| rights:', record['rights_status'])
            req = urllib.request.Request(record['pdf_url'], headers={'User-Agent': 'LinkPaper-Research-Collection/0.1'})
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read(64 * 1024 * 1024 + 1)
            if len(data) > 64 * 1024 * 1024 or not data.startswith(b'%PDF-'):
                raise SystemExit('Unexpected response for ' + record['source_id'])
            if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
                raise SystemExit('Publisher bytes changed; inspect version instead of silently replacing manifest: ' + record['source_id'])
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix('.pdf.part')
            temporary.write_bytes(data)
            os.replace(temporary, path)
        data = path.read_bytes()
        if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
            raise SystemExit('Integrity mismatch: ' + record['source_id'])
        print('OK', record['source_id'], len(data), record['sha256'])


if __name__ == '__main__':
    main()
