#!/bin/bash
# -----------------------------------------------------------------------------
# Blaze training-log vault export
#
# Pulls log.json straight off the SiteGround server over SSH (no PIN needed —
# SSH key IS the auth) and commits it to the local cycle library, so your
# training history is versioned over time.
#
# Usage:  ./export-log.sh          # pull + commit if changed
#         ./export-log.sh --push   # also push to the GitHub vault branch
# -----------------------------------------------------------------------------
set -euo pipefail

KEY="$HOME/.ssh/siteground_crossfitblaze2"
HOST="u184-thjfytvg5meh@gvam1155.siteground.biz"
PORT=18765
REMOTE="~/www/crossfitblaze.com/private/blaze-log/log.json"
LIB="$HOME/blaze-cycles"
DEST="$LIB/log/log.json"

mkdir -p "$LIB/log"

if ! scp -q -o BatchMode=yes -o ConnectTimeout=20 -i "$KEY" -P "$PORT" \
        "$HOST:$REMOTE" "$DEST.new" 2>/dev/null; then
  echo "No log on server yet (or SSH unavailable) — nothing to export."
  rm -f "$DEST.new"
  exit 0
fi

# refuse to overwrite good data with a truncated/corrupt pull
if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$DEST.new" 2>/dev/null; then
  echo "ERROR: pulled file is not valid JSON — keeping previous export." >&2
  rm -f "$DEST.new"
  exit 1
fi

mv "$DEST.new" "$DEST"

# human-readable summary alongside the raw JSON
python3 - "$DEST" "$LIB/log/SUMMARY.md" <<'PY'
import json, sys, collections
log  = json.load(open(sys.argv[1]))
out  = open(sys.argv[2], "w")
sess = log.get("sessions", {})
out.write("# Blaze Training Log\n\n")
out.write(f"Sessions recorded: **{len(sess)}**\n\n")
for cid, c in sorted(log.get("cycles", {}).items()):
    out.write(f"- **{cid}** — currently week {c.get('week','?')}\n")
tm = log.get("tm", {})
if tm:
    out.write("\n## Training maxes\n\n")
    for lift, t in sorted(tm.items()):
        if t.get("v") is not None:
            out.write(f"- {lift}: {t['v']} lb\n")
by_day = collections.defaultdict(list)
for key in sorted(sess):
    date, cycle, day = (key.split("|") + ["", ""])[:3]
    by_day[date].append((cycle, day, sess[key]))
out.write("\n## Sessions\n")
for date in sorted(by_day, reverse=True):
    for cycle, day, s in by_day[date]:
        out.write(f"\n### {date} — {cycle} / {day} (week {s.get('week','?')})\n\n")
        for ex, sets in (s.get("ex") or {}).items():
            done = [f"{x.get('w')}×{x.get('r')}" for x in sets if x and x.get("w") is not None]
            if done:
                out.write(f"- **{ex}**: {', '.join(done)}\n")
        for ex, note in (s.get("notes") or {}).items():
            out.write(f"  - _{ex}: {note}_\n")
out.close()
print("summary written")
PY

cd "$LIB"
if git diff --quiet -- log/ 2>/dev/null && git diff --cached --quiet -- log/ 2>/dev/null; then
  if [ -z "$(git status --porcelain log/)" ]; then
    echo "No training-log changes since last export."
    exit 0
  fi
fi

git add log/
git -c user.name='Blazefit' -c user.email='jason@crossfitblaze.com' \
    commit -q -m "Training log export $(date +%Y-%m-%d)"
echo "Committed training-log export."

if [ "${1:-}" = "--push" ]; then
  git push -q origin HEAD && echo "Pushed."
fi
