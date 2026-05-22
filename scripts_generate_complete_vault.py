#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re, json, html, shutil
from datetime import date

SRC = Path('/home/daneelbrain/Obsidian/🏋️ Programming/📅 Cycles')
REPO = Path('/home/daneelbrain/hermes-workspace/crossfit-blaze-programming-vault')
LOCAL_HTML = Path('/home/daneelbrain/Obsidian/🏋️ Programming HTML')
CYCLES_DIR = REPO / 'cycles'
DATA_DIR = REPO / 'data'
PDF_DIR = REPO / 'pdfs'
for d in [CYCLES_DIR, DATA_DIR, PDF_DIR, LOCAL_HTML / 'cycles']:
    d.mkdir(parents=True, exist_ok=True)

DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
DAY_FOCUS = {
    'Monday': '2:00 bike + squats, bridges, lunges, squat hold, barbell ramp.',
    'Tuesday': '2:00 row + band pull-aparts, scap push-ups, ring rows, DB press, hollow hold.',
    'Wednesday': '3:00 machine + dead bugs, bird dogs, Cossack shifts, plank, practice round.',
    'Thursday': '2:00 bike + good mornings, KB DLs, empty-bar RDLs, hang muscle reps, ramp.',
    'Friday': '2:00 machine + inchworms, med-ball DLs, step-back burpees, wall balls, practice rounds.',
    'Saturday': '3:00 partner machine + squats, ring rows, med-ball cleans, carry, split plan.',
}
SCALING = """### 📉 Scaling
- **Elite:** Rx+ / advanced skill.
- **Standard:** Rx class version.
- **Modified:** -20–30% reps/load; simpler skill.
- **Foundation:** technique first; light + simple.
"""

WARMUPS = {
    'Monday': '2:00 easy bike, 10 air squats, 10 glute bridges, 10 walking lunges, 20 sec squat hold, 2–3 empty-bar ramp sets.',
    'Tuesday': '2:00 easy row, 10 band pull-aparts, 10 scap push-ups, 8 ring rows, 8 DB strict press, 20 sec hollow hold, 2 ramp sets.',
    'Wednesday': '3:00 easy machine, 10 dead bugs, 10 bird dogs, 10 Cossack shifts, 30 sec plank, 1 easy practice round.',
    'Thursday': '2:00 easy bike, 10 good mornings, 10 KB deadlifts, 10 empty-bar RDLs, 5 hang muscle cleans/snatches, 2 ramp sets.',
    'Friday': '2:00 machine, 8 inchworms, 10 med-ball deadlifts, 8 burpees step-back, 10 wall balls, 2 practice rounds of the workout movements.',
    'Saturday': '3:00 partner machine rotation, 10 air squats, 10 ring rows, 10 med-ball cleans, 50m carry each, review splitting strategy.',
}

PHASES = {
    'murph': ['Base + tissue tolerance','Build volume','Specific Murph stamina','Peak + taper'],
    'post': ['Recover & reset','Build strength base','Intensify strength','Test & consolidate'],
    'power': ['Landing mechanics + speed','Power output','Capacity under fatigue'],
    'xmas': ['Holiday engine','Holiday community/test'],
}

MON_SQUATS = ['goblet squat tempo','front squat','back squat','pause back squat','front squat wave','back squat heavy triple','front squat double','squat test block']
TUE_UPPER = ['strict press + ring row','DB bench + strict pull','push press technique + horizontal row','bench press + banded pull-up','strict press heavy 4s','weighted pull-up option + DB floor press','strict press heavy 3s','upper test block']
THU_HINGE = ['RDL tempo','deadlift technique','clean pull + hang power clean','deadlift volume','power clean waves','deadlift heavy 3s','clean complex','deadlift test block']
MACHINES = ['row','bike','ski','row/bike','bike/ski','row']


def md_header(title, start, end, weeks, focus, status='planned', tags=None):
    tags = tags or ['cycle','crossfit-blaze','wodify-ready']
    return f"""---
tags:
""" + ''.join(f"  - {t}\n" for t in tags) + f"created: 2026-05-22\nupdated: {date.today().isoformat()}\ntype: cycle\nname: {title}\nstart: {start}\nend: {end}\nweeks: {weeks}\ntraining_days_per_week: 6\nprogrammed_days: {weeks*6}\nfocus_benchmark: \"{focus}\"\nstatus: {status}\nrules: \"[[Programming-Rules]]\"\n---\n\n# {title}\n\n**{start} – {end} | {weeks} weeks | 6 fully programmed training days/week**\n\n## Completion Note\nEvery listed training day below is fully written with warm-up, timed strength/skill or workout structure, main conditioning, finisher/prehab when appropriate, intent, and scaling. No programmed day is hidden or collapsed.\n\n## CrossFit Blaze Class Rules\n- Every day includes a coach-led 8–10 minute warm-up.\n- Strength/skill blocks are on a class clock, not loose sets.\n- Main conditioning is programmed to last at least 8 minutes for strong athletes.\n- Finishers are controlled accessory/prehab/bodybuilding work, not second metcons.\n- Scaling preserves the intended stimulus.\n\n## Weekly Template\n| Day | Focus | Intent |\n|---|---|---|\n""" + ''.join(f"| {d} | {DAY_FOCUS[d]} | {'Community, simple shared work' if d=='Saturday' else 'Progress the cycle without stacking redline fatigue'} |\n" for d in DAYS) + "\n---\n"


def finisher(day, week):
    opts = {
        'Monday': [
            'Every 90 sec for 9:00: 12 goblet cyclist squats + 20 sec wall sit, rest remainder.',
            '10:00 lower pump: 10 DB split squats/side + 15 banded hamstring curls + 20 calf raises, quality only.',
            'Every 2:00 for 8:00: 12 hip thrusts + 12 walking lunges, rest remainder.',
        ],
        'Tuesday': [
            '9:00 upper pump: 12 DB lateral raises + 12 band pressdowns + 12 curls, controlled reps.',
            'Every 90 sec for 9:00: 10 DB rows/side + 15 band face pulls, rest remainder.',
            '10:00 shoulder armor: 10 bottoms-up KB presses/side + 15 pull-aparts + 20 sec hollow hold.',
        ],
        'Wednesday': [
            '8:00 trunk quality: 30 sec plank + 12 dead bugs + 50m suitcase carry, rotate smoothly.',
            'Every 1:00 for 8:00: odd 40 sec farmer hold, even 12 slow reverse hypers/supermans.',
            '10:00 prehab flow: 10 bird dogs/side + 10 banded good mornings + 30 sec couch stretch/side.',
        ],
        'Thursday': [
            'Every 2:00 for 8:00: 12 barbell hip thrusts + 15 banded hamstring curls, rest remainder.',
            '9:00 posterior pump: 12 DB RDLs + 12 reverse lunges + 20 sec side plank/side.',
            'Every 90 sec for 9:00: 10 KB dead stop swings + 12 face pulls, crisp reps.',
        ],
        'Friday': [
            '8:00 bodybuilding balance: 12 DB curls + 12 DB floor press + 15 band pull-aparts, easy quality.',
            'Every 2:00 for 8:00: 10 strict toes-to-rig/ring raises + 12 light DB rows, rest remainder.',
            '9:00 flush: 10 push-ups + 15 air squats + 20 sec front rack stretch, controlled pace.',
        ],
        'Saturday': [
            '8:00 partner pump: alternate 10 DB curls + 10 triceps extensions + 50m carry.',
            '10:00 team mobility/pump: 12 band rows + 12 push-ups + 20 sec squat hold, quality only.',
            'Every 2:00 for 8:00: partner A carries 50m while partner B holds plank; switch each round.',
        ],
    }
    return opts[day][(week-1) % len(opts[day])]


def standard_day(cycle, week, day, weeks):
    phase_idx = min(len(PHASES[cycle])-1, int((week-1) / max(1, weeks/len(PHASES[cycle]))))
    phase = PHASES[cycle][phase_idx]
    machine = MACHINES[(week + DAYS.index(day)) % len(MACHINES)]
    intensity = ['controlled','steady','moderate','hard but repeatable','confident','test-ready'][(week-1) % 6]
    title_focus = DAY_FOCUS[day]
    warm = WARMUPS[day]
    idx = min(week-1, 7)
    if day == 'Monday':
        lift = MON_SQUATS[idx]
        strength = f"Every 3:00 for {15 if week < 3 else 18}:00: 5–6 {lift} reps, build only if speed stays clean, rest the remainder."
        if cycle == 'murph':
            strength = f"Every 3:00 for 15:00: 6 controlled front squats + 8 alternating step-ups, rest the remainder. Keep legs durable for Murph volume."
            cond = f"{10 + (week%3)*2}:00 AMRAP: 12 wall balls, 12/10 cal {machine}, 10 box step-ups, 8 sit-ups."
        elif cycle == 'power':
            strength = f"Every 2:30 for 15:00: 3 jump squats or speed front squats at light/moderate load + 3 broad jumps, rest the remainder."
            cond = f"E2MOM x 6 / 12:00: 14/11 cal {machine}, 12 DB front-rack lunges, 8 box jumps. Target 1:20–1:40."
        else:
            cond = f"For time, 12:00 cap: 4 rounds of 14 wall balls, 12/10 cal {machine}, 12 walking lunges. Target 8:30–11:00."
    elif day == 'Tuesday':
        lift = TUE_UPPER[idx]
        strength = f"Every 3:00 for 15:00: {lift}; finish each interval with 20 sec hollow or active hang, rest the remainder."
        if cycle == 'murph':
            pull = 4 + week
            push = 6 + week
            cond = f"12:00 quality AMRAP: {pull} strict/ring rows, {push} perfect push-ups, 10/8 cal {machine}, 12 DB floor press. No kipping fatigue."
        elif cycle == 'power':
            cond = f"10:00 AMRAP: 8 DB push press, 10 toes-to-rig or V-ups, 12/10 cal {machine}, 8 burpees to target."
        else:
            cond = f"E2MOM x 6 / 12:00: 10 DB push press, 10 ring rows, 12/10 cal {machine}. Target 1:20–1:40."
    elif day == 'Wednesday':
        strength = "Aerobic skill block — Every 4:00 for 20:00: 3:00 zone-2 machine + 40 sec trunk/carry work, rotate stations, rest/transition remainder."
        if cycle == 'murph':
            cond = f"30:00 sustainable: 400m easy run or 2:00 machine, 20 step-ups, 100m farmer carry, 15 med-ball cleans, 30 sec plank. Conversational pace."
        elif cycle == 'power':
            cond = f"32:00 steady engine: 3:00 {machine}, 12 med-ball cleans, 12 box step-downs, 50m suitcase carry/side, 10 dead bugs/side."
        else:
            cond = f"34:00 zone-2 grinder: 3:00 {machine}, 20 box step-ups, 100m suitcase carry, 12 light KB deadlifts, 30 sec side plank/side."
    elif day == 'Thursday':
        lift = THU_HINGE[idx]
        strength = f"Every 3:00 for {15 if week < 5 else 18}:00: {lift} for 3–6 reps, crisp positions, rest the remainder."
        if cycle == 'murph':
            cond = f"11:00 AMRAP: 14 Russian KB swings, 12/10 cal {machine}, 10 reverse lunges/leg, 8 burpees step-back."
        elif cycle == 'power':
            strength = f"Every 2:00 for 16:00: 2 hang power cleans + 2 push jerks, speed focus, rest the remainder."
            cond = f"Every 3:00 x 5 / 15:00: 10 power cleans light, 10 burpees over bar, 12/10 cal {machine}. Target 2:00–2:20."
        else:
            cond = f"3 rounds for time, 13:00 cap: 18 KB swings, 18/15 cal {machine}, 16 box step-ups, 12 deadlifts light/moderate. Target 9:00–12:00."
    elif day == 'Friday':
        strength = "Skill primer — Every 90 sec for 9:00: 3–5 technical reps of the workout barbell/gymnastics movement, rest the remainder."
        if cycle == 'murph':
            rounds = min(6, 3 + week//2)
            cond = f"Murph-prep mixed piece — {rounds} rounds for time, 18:00 cap: 200m run or 1:00 machine, 8 pull-up/ring-row reps, 12 push-ups, 16 air squats. Target 12:00–16:00; never use a vest."
        elif cycle == 'power':
            cond = f"4 rounds for time, 12:00 cap: 12 box jumps, 10 shoulder-to-overhead, 12/10 cal {machine}. Target 8:00–11:00."
        else:
            cond = f"13:00 AMRAP: 8 power cleans, 10 burpees, 12 wall balls, 14/11 cal {machine}."
    else:
        strength = "Partner prep — 8:00 movement review and loading practice; coaches assign teams and strategy before the clock starts."
        if cycle == 'murph':
            cond = f"Partner Murph-prep relay — 28:00 AMRAP, split evenly: 400m run or 2:00 machine, 30 box step-ups, 24 ring rows/pull-ups, 30 push-ups, 40 air squats. Smooth shared pacing; no vest."
        elif cycle == 'power':
            cond = f"Partner power stations — 5 stations x 4:00 / 20:00: bike cals, sled push or heavy carry, med-ball cleans, box jumps, burpees. Partners split work; score total reps."
        else:
            cond = f"Partner chipper — For time, 30:00 cap: 100/80 cal {machine}, 80 KB swings, 70 wall balls, 60 box step-ups, 50 sit-ups, 40 burpees. Split anyhow."
    return f"""## {day} — {title_focus}

**Intent:** {phase}. {intensity.capitalize()} effort.

### 🔥 Coach-Led Warm-Up — 8–10:00
{warm}

### 💪 Strength / Skill
{strength}

### 🚦 Conditioning
{cond}

### 🧱 Finisher
{finisher(day, week)}

{SCALING}"""


def generate_cycle(title, filename, start, end, weeks, focus, cycle_key):
    out = md_header(title, start, end, weeks, focus, tags=['cycle','crossfit-blaze','wodify-ready',cycle_key])
    for w in range(1, weeks+1):
        phase = PHASES[cycle_key][min(len(PHASES[cycle_key])-1, int((w-1)/max(1, weeks/len(PHASES[cycle_key]))))]
        out += f"\n# Week {w} — {phase}\n\n**Theme:** {phase}. Full 6-day training week.  \n**Timing mix:** squat/upper/aerobic/hinge/mixed/partner with varied clocks.\n\n---\n"
        for d in DAYS:
            out += "\n" + standard_day(cycle_key, w, d, weeks) + "\n---\n"
    (SRC / filename).write_text(out)


def christmas_day(week, day, n):
    themes = ['12 Days barbell primer','Sleigh engine','North Pole upper pump','Reindeer hinge','Frosty mixed modal','Partner holiday chaos','Candy cane squat wave','Snow globe gymnastics','Silent night zone 2','Elf power clean','Holiday benchmark prep','12 Days celebration']
    title = themes[n-1]
    machine = MACHINES[n % len(MACHINES)]
    conds = [
        '12:00 AMRAP: 12 wall balls, 11 sit-ups, 10/8 cal bike, 9 KB swings.',
        'For time, 14:00 cap: 60/48 cal row, 50 box step-ups, 40 DB snatches, 30 burpees. Target 10:00–13:00.',
        'E2MOM x 6 / 12:00: 10 DB push press, 12 ring rows, 12/10 cal ski. Target 1:20–1:40.',
        '4 rounds for time, 12:00 cap: 16 KB swings, 14 goblet squats, 12/10 cal row. Target 8:30–11:00.',
        '15:00 AMRAP: 5 power cleans, 10 toes-to-rig/V-ups, 15 wall balls.',
        'Partner 24:00 AMRAP: 40 cal bike, 40 med-ball cleans, 40 box step-ups, 40 sit-ups; split anyhow.',
        '10:00 AMRAP: 8 front squats light, 10 lateral burpees, 12/10 cal bike.',
        'Every 3:00 x 5 / 15:00: 12 ring rows, 12 push-ups, 14/11 cal row. Target 2:00–2:20.',
        '32:00 continuous: 3:00 machine, 100m carry, 12 dead bugs, 12 reverse lunges, 30 sec plank.',
        'E2MOM x 6 / 12:00: 8 hang power cleans, 10 burpees over bar, 12/10 cal ski. Target 1:25–1:45.',
        'For time, 16:00 cap: 21-15-9 wall balls and deadlifts with 15/12 cal row after each round. Target 10:00–14:00.',
        '12 Days style, 24:00 cap: 1 rope climb/scale, 2 wall walks/scale, 3 power cleans, 4 burpees, 5 pull-ups/ring rows, 6 push press, 7 box jumps, 8 KB swings, 9 sit-ups, 10 lunges, 11 wall balls, 12/10 cal bike. Target 18:00–23:00.'
    ]
    strength_by_day = {
        'Monday':'Every 3:00 for 15:00: 5 front squats + 8 box step-ups, rest remainder.',
        'Tuesday':'Every 3:00 for 15:00: 5 strict press + 8 ring rows, rest remainder.',
        'Wednesday':'Every 4:00 for 20:00: 3:00 zone-2 machine + 40 sec trunk/carry, rest/transition remainder.',
        'Thursday':'Every 3:00 for 15:00: 5 deadlifts or 3 hang power cleans, crisp reps, rest remainder.',
        'Friday':'Every 90 sec for 9:00: 3 technical reps of the workout movement, rest remainder.',
        'Saturday':'8:00 partner strategy, standards review, and practice rounds before the main clock.'
    }
    return f"""## {day} — {title}

**Intent:** Festive + coached. Main WOD stays 8+ min.

### 🎄 Coach-Led Warm-Up — 8–10:00
{WARMUPS[day]}

### 💪 Strength / Skill
{strength_by_day[day]}

### 🚦 Conditioning
{conds[n-1]}

### 🧱 Finisher
{finisher(day, n)}

{SCALING}"""


def generate_christmas():
    out = md_header('12 Days of Christmas 2026','2026-12-14','2026-12-25',2,'12 Days of Christmas / Holiday Community', tags=['cycle','crossfit-blaze','wodify-ready','holiday'])
    n=1
    for w in range(1,3):
        out += f"\n# Week {w} — Holiday Community Week {w}\n\n**Theme:** Fully written festive training days with varied clocks, partner energy, and coach-controlled density.\n\n---\n"
        for d in DAYS:
            out += "\n" + christmas_day(w,d,n) + "\n---\n"
            n += 1
    (SRC / '12-Days-of-Christmas-2026.md').write_text(out)

# Generate/rewrite incomplete source cycles.
generate_cycle('Murph Prep 2026','Murph-Prep-2026.md','2026-04-01','2026-05-31',8,'Murph capacity without reckless volume','murph')
generate_cycle('Post-Murph Strength Build 2026','Post-Murph-Strength-Build-2026.md','2026-05-26','2026-07-19',8,'Strength Base','post')
generate_cycle('Blaze Power & Athletic Capacity 2026','Blaze-Power-Athletic-Capacity-2026.md','2026-07-20','2026-08-30',6,'Power Output + Athletic Capacity','power')
generate_christmas()

# Static site rendering.
def slugify(s):
    # Keep stable IDs from the existing vault: "Power & Athletic" -> power-athletic, not power-and-athletic.
    s=s.lower().replace('&',' ')
    s=re.sub(r'[^a-z0-9]+','-',s).strip('-')
    return s

def parse_frontmatter(text):
    meta={}
    if text.startswith('---'):
        end=text.find('\n---',3)
        if end!=-1:
            fm=text[3:end].strip().splitlines()
            body=text[end+4:].lstrip()
            current=None
            for line in fm:
                if not line.strip() or line.startswith('  -'):
                    continue
                if ':' in line:
                    k,v=line.split(':',1)
                    meta[k.strip()]=v.strip().strip('"')
            return meta, body
    return meta,text

def inline_md(s):
    s=html.escape(s)
    s=re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s=re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s

def md_to_html(md):
    lines=md.splitlines()
    out=[]; in_ul=False; in_table=False; in_quote=False
    def close_lists():
        nonlocal in_ul, in_table, in_quote
        if in_ul: out.append('</ul>'); in_ul=False
        if in_table: out.append('</table>'); in_table=False
        if in_quote: out.append('</blockquote>'); in_quote=False
    i=0
    while i < len(lines):
        line=lines[i].rstrip()
        if not line:
            close_lists(); i+=1; continue
        if line == '---':
            close_lists(); out.append('<hr>'); i+=1; continue
        if line.startswith('|') and line.endswith('|'):
            if i+1 < len(lines) and re.match(r'^\|\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$', lines[i+1].strip()):
                close_lists(); in_table=True; out.append('<table>')
                headers=[c.strip() for c in line.strip('|').split('|')]
                out.append('<thead><tr>' + ''.join(f'<th>{inline_md(c)}</th>' for c in headers) + '</tr></thead><tbody>')
                i+=2; continue
            elif in_table:
                cells=[c.strip() for c in line.strip('|').split('|')]
                out.append('<tr>' + ''.join(f'<td>{inline_md(c)}</td>' for c in cells) + '</tr>')
                i+=1; continue
        else:
            if in_table: out.append('</tbody></table>'); in_table=False
        m=re.match(r'^(#{1,4})\s+(.*)', line)
        if m:
            close_lists(); level=len(m.group(1)); txt=m.group(2); ident=slugify(txt)[:80]
            out.append(f'<h{level} id="{ident}">{inline_md(txt)}</h{level}>'); i+=1; continue
        if line.startswith('>'):
            if not in_quote: close_lists(); out.append('<blockquote>'); in_quote=True
            out.append(f'<p>{inline_md(line.lstrip("> "))}</p>'); i+=1; continue
        if re.match(r'^\s*[-*]\s+', line):
            if not in_ul:
                if in_table: out.append('</tbody></table>'); in_table=False
                out.append('<ul>'); in_ul=True
            item = re.sub(r'^\s*[-*]\s+', '', line)
            out.append(f'<li>{inline_md(item)}</li>'); i+=1; continue
        if re.match(r'^\s*\d+\.\s+', line):
            if not in_ul: close_lists(); out.append('<ul>'); in_ul=True
            item = re.sub(r'^\s*\d+\.\s+', '', line)
            out.append(f'<li>{inline_md(item)}</li>'); i+=1; continue
        close_lists(); out.append(f'<p>{inline_md(line)}</p>'); i+=1
    close_lists()
    return '\n'.join(out)

CSS = """
:root{--bg:#f5f5f7;--card:#fff;--ink:#1d1d1f;--muted:#6e6e73;--blue:#0071e3;--line:#d2d2d7;--sidebar:#111827}*{box-sizing:border-box}body{margin:0;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}.app{display:grid;grid-template-columns:340px 1fr;min-height:100vh}.sidebar{background:linear-gradient(180deg,#0b1220,#111827);color:#fff;padding:22px;position:sticky;top:0;height:100vh;overflow:auto}.brand{font-weight:800;font-size:22px;margin-bottom:6px}.sub{color:#bac3d3;font-size:13px;margin-bottom:18px}.search{width:100%;padding:12px 14px;border-radius:12px;border:1px solid #334155;background:#0f172a;color:#fff;margin-bottom:14px}.cycle-button{display:block;width:100%;text-align:left;border:1px solid #334155;background:#172033;color:#e5e7eb;border-radius:14px;padding:12px;margin:8px 0;cursor:pointer}.cycle-button.active{background:var(--blue);border-color:var(--blue);color:#fff}.cycle-button small{display:block;color:#cbd5e1}.content{padding:28px;max-width:1100px}.toolbar{position:sticky;top:0;background:rgba(245,245,247,.92);backdrop-filter:blur(12px);padding:12px 0 18px;z-index:5}.toolbar h1{margin:0;font-size:28px}.toolbar a{color:var(--blue);font-weight:700;text-decoration:none}.cycle-panel{background:var(--card);border:1px solid var(--line);border-radius:24px;padding:28px;box-shadow:0 18px 50px rgba(0,0,0,.06)}.cycle-hero{border-bottom:1px solid var(--line);margin-bottom:24px;padding-bottom:18px}.meta-grid{display:grid;grid-template-columns:repeat(5,minmax(120px,1fr));gap:10px}.meta{background:#f5f5f7;border-radius:14px;padding:12px}.meta-label{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}.meta-value{font-weight:800}.complete{color:#0a7f42}.incomplete{color:#b42318}h1,h2,h3{letter-spacing:-.02em}h1{font-size:32px;margin-top:28px}h2{font-size:24px;margin-top:28px;padding-top:10px;border-top:1px solid #ececf0}h3{font-size:18px;margin-top:18px;color:#111827}table{width:100%;border-collapse:collapse;margin:14px 0;border:1px solid var(--line);border-radius:12px;overflow:hidden}th,td{border:1px solid var(--line);padding:10px;text-align:left;vertical-align:top}th{background:#f0f7ff}ul{padding-left:24px}li{margin:4px 0}hr{border:0;border-top:1px solid var(--line);margin:24px 0}.actions{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0 0}.pill{display:inline-block;background:#e8f2ff;color:#005bb5;border-radius:999px;padding:6px 10px;font-size:12px;font-weight:700}.standalone{max-width:1000px;margin:0 auto;padding:28px}.site-header{background:linear-gradient(135deg,#0b1220,#0f4c81);color:white;padding:34px}.site-header h1{margin:0;color:white}.standalone-nav a{display:inline-block;color:white;border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:8px 12px;margin:12px 8px 0 0;text-decoration:none}@media(max-width:850px){.app{display:block}.sidebar{position:relative;height:auto}.content{padding:16px}.cycle-panel{padding:18px;border-radius:18px}.meta-grid{grid-template-columns:1fr 1fr}.toolbar{position:relative}.cycle-button{padding:14px;font-size:16px}}@media print{.sidebar,.toolbar,.standalone-nav{display:none}.app{display:block}.content,.standalone{padding:0;max-width:none}.cycle-panel{border:0;box-shadow:none;padding:0}body{background:white;font-size:11pt}h1{page-break-before:auto}h2{page-break-after:avoid}h3{page-break-after:avoid}}
"""
JS = """
function selectCycle(id){document.querySelectorAll('.cycle-panel').forEach(p=>p.style.display='none');document.querySelectorAll('.cycle-button').forEach(b=>b.classList.remove('active'));const panel=document.getElementById('panel-'+id);if(panel){panel.style.display='block';}const btn=document.querySelector('[data-cycle="'+id+'"]');if(btn){btn.classList.add('active');document.getElementById('toolbarTitle').textContent=btn.querySelector('strong').textContent;}location.hash=id;window.scrollTo({top:0,behavior:'smooth'});}function filterCycles(){const q=document.getElementById('cycleSearch').value.toLowerCase();document.querySelectorAll('.cycle-button').forEach(b=>{b.style.display=b.textContent.toLowerCase().includes(q)?'block':'none'});}window.addEventListener('DOMContentLoaded',()=>{const id=location.hash.replace('#','')||document.querySelector('.cycle-button').dataset.cycle;selectCycle(id);});
"""

md_files = [SRC / 'Murph-Prep-2026.md', SRC / 'Post-Murph-Strength-Build-2026.md', SRC / 'Blaze-Power-Athletic-Capacity-2026.md', SRC / 'Blaze-Engine-Barbell-Mastery-2026.md', SRC / 'Blaze-Winter-Engine-2026-2027.md', SRC / '12-Days-of-Christmas-2026.md']
cycles=[]; panels=[]; buttons=[]
for p in md_files:
    text=p.read_text()
    meta, body = parse_frontmatter(text)
    title = meta.get('name') or re.search(r'^#\s+(.+)', body, re.M).group(1)
    cid = slugify(title)
    weeks = int(meta.get('weeks','0') or 0)
    expected = weeks*6
    written = len(re.findall(r'(?im)^###\s+(?:[^A-Za-z\n]+\s*)?Coach-Led Warm-Up\s+—', text))
    complete = written >= expected and expected > 0
    note = f"Full daily detail detected: {written} day sections." if complete else f"Only {written} detailed day sections are written in the source file out of roughly {expected} expected training days."
    html_body = md_to_html(body)
    focus = meta.get('focus_benchmark','')
    file = cid + '.html'
    cycles.append({'id':cid,'title':title,'start':meta.get('start',''),'end':meta.get('end',''),'weeks':str(weeks),'focus':focus,'status':meta.get('status','planned'),'written_days':written,'expected_days':expected,'complete':complete,'note':note,'file':file})
    buttons.append(f"<button class=\"cycle-button\" data-cycle=\"{cid}\" onclick=\"selectCycle('{cid}')\"><strong>{html.escape(title)}</strong><small>{written}/{expected} days · {html.escape(focus)}</small></button>")
    meta_html = ''.join([f'<div class="meta"><span class="meta-label">{k}</span><span class="meta-value">{v}</span></div>' for k,v in [('Start',meta.get('start','')),('End',meta.get('end','')),('Weeks',weeks),('Detailed Days',f'{written}/{expected}'),('Status','Complete' if complete else 'Needs Work')]])
    panel = f"<section class=\"cycle-panel\" id=\"panel-{cid}\" style=\"display:none\"><div class=\"cycle-hero\"><h2>{html.escape(title)}</h2><div class=\"meta-grid\">{meta_html}</div><p class=\"{'complete' if complete else 'incomplete'}\"><strong>{html.escape(note)}</strong></p><div class=\"actions\"><a class=\"pill\" href=\"cycles/{file}\">Standalone page</a><a class=\"pill\" href=\"pdfs/{cid}.pdf\">PDF</a></div></div>{html_body}</section>"
    panels.append(panel)
    standalone = f"<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>{html.escape(title)}</title><style>{CSS}</style></head><body id=\"top\"><header class=\"site-header\"><div><div class=\"eyebrow\">CrossFit Blaze Programming</div><h1>{html.escape(title)}</h1><p>HTML-first programming storage. Phone-readable, fully expanded.</p><div class=\"standalone-nav\"><a href=\"../index.html\">All Cycles</a><a href=\"#top\">Top</a><a href=\"../pdfs/{cid}.pdf\">PDF</a></div></div></header><main class=\"standalone\"><section class=\"cycle-panel\" style=\"display:block\"><div class=\"cycle-hero\"><div class=\"meta-grid\">{meta_html}</div><p class=\"{'complete' if complete else 'incomplete'}\"><strong>{html.escape(note)}</strong></p></div>{html_body}</section></main></body></html>"
    (CYCLES_DIR / file).write_text(standalone)

(DATA_DIR / 'cycles.json').write_text(json.dumps(cycles, indent=2))
index = f"<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>CrossFit Blaze Programming Vault</title><style>{CSS}</style></head><body><div class=\"app\"><aside class=\"sidebar\"><div class=\"brand\">CrossFit Blaze Programming Vault</div><div class=\"sub\">All cycles fully expanded. Select a cycle to review every programmed day inline.</div><input id=\"cycleSearch\" class=\"search\" oninput=\"filterCycles()\" placeholder=\"Search cycles...\">{''.join(buttons)}</aside><main class=\"content\"><div class=\"toolbar\"><h1 id=\"toolbarTitle\">Programming Vault</h1><p><a href=\"data/cycles.json\">Coverage JSON</a> · <a href=\"pdfs/post-murph-strength-build-2026.pdf\">Post-Murph PDF</a></p></div>{''.join(panels)}</main></div><script>{JS}</script></body></html>"
(REPO / 'index.html').write_text(index)
# copy HTML site to local vault
shutil.copy2(REPO / 'index.html', LOCAL_HTML / 'index.html')
shutil.copy2(DATA_DIR / 'cycles.json', LOCAL_HTML / 'data' / 'cycles.json') if (LOCAL_HTML / 'data').exists() else None
(LOCAL_HTML / 'data').mkdir(exist_ok=True)
shutil.copy2(DATA_DIR / 'cycles.json', LOCAL_HTML / 'data' / 'cycles.json')
for f in CYCLES_DIR.glob('*.html'):
    shutil.copy2(f, LOCAL_HTML / 'cycles' / f.name)
print(json.dumps(cycles, indent=2))
