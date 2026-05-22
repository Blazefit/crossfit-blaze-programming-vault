#!/usr/bin/env python3
from pathlib import Path
import re, json, sys
SRC=Path('/home/daneelbrain/Obsidian/🏋️ Programming/📅 Cycles')
REPO=Path('/home/daneelbrain/hermes-workspace/crossfit-blaze-programming-vault')
cycles=json.loads((REPO/'data/cycles.json').read_text())
fail=[]
for c in cycles:
    print(f"{c['title']}: {c['written_days']}/{c['expected_days']} detailed days complete={c['complete']}")
    if c['written_days'] != c['expected_days'] or not c['complete']:
        fail.append(f"coverage {c['title']}")
# robust source count
for p in SRC.glob('*.md'):
    text=p.read_text()
    weeks=re.search(r'weeks:\s*(\d+)', text)
    expected=int(weeks.group(1))*6 if weeks else None
    warm=len(re.findall(r'(?im)^###\s+Coach-Led Warm-Up\s+—', text))
    print(f"SOURCE {p.name}: warmups={warm} expected={expected}")
    if expected and warm != expected:
        fail.append(f"source warmup count {p.name} {warm}!={expected}")
    # detect explicit main conditioning clocks under 8 min (exclude finisher/prehab lines)
    for m in re.finditer(r'(?im)^###\s+Conditioning\s*\n([^#]+?)(?=\n###|\n---|\Z)', text):
        block=m.group(1)
        # Check true total durations/caps only. Ignore interval counts (x 6) and station length when an explicit total is >=8.
        totals = []
        for pat in [r'(?i)(\d{1,2}):00\s*(?:AMRAP|EMOM|cap|total)', r'(?i)/(?:\s*)(\d{1,2}):00', r'(?i)(\d{1,2}):00\s+cap', r'(?i)(\d{1,2}):00\s+continuous']:
            totals += [int(x) for x in re.findall(pat, block)]
        # Phrases like "5 stations x 4:00 / 20:00 total" are okay because total=20.
        if totals and max(totals) < 8:
            fail.append(f"sub8 conditioning total in {p.name}: totals={totals} in {block[:120]!r}")
if fail:
    print('\nFAIL')
    print('\n'.join(fail))
    sys.exit(1)
print('\nPASS: all cycles have exact expected detailed-day coverage and no obvious sub-8 main conditioning clocks.')
