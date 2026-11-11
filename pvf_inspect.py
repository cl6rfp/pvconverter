from __future__ import annotations
import argparse, json
from pvf import read_pvf

ap=argparse.ArgumentParser(description='Inspect and verify a PVF file')
ap.add_argument('file')
args=ap.parse_args()
r=read_pvf(args.file)
print(f'PVF {r["version"][0]}.{r["version"][1]} | {r["file_size"]:,} bytes | {len(r["blocks"])} blocks')
for name,b in r['blocks'].items():
    d=b['data']
    if isinstance(d,list): count=len(d)
    else: count=b['record_count']
    print(f'{name:4} records={count:,} schema={b["schema_version"]}')
print('Integrity: OK')
