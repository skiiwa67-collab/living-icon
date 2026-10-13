#!/bin/bash
# Living Icon loop (Chris-approved exception; same loop, no cron). Box-local only. ONE process.
#  - singleton: flock on $LI_LOCK (default /tmp/living-icon-loop.v2.lock) + pidfile; a second copy exits at once
#  - every 5 s tick, in order: derive_eve_state.py --once (single non-looping Eve pass; no separate deriver),
#    then sync_live_moods.py (mirror each bot's own file -> docs/status/live, hold expiry, OK overlay)
#  - every 600 s: refresh_data.py (data.json + both feed.json, atomic)
#  - logs > 5 MB are truncated to their last 1 MB
# Test knobs (env): LI_DIR LI_LOGS LI_LOCK LI_PIDFILE LI_SLEEP LI_MAX_TICKS LI_DERIVE LI_SYNC LI_REFRESH
LOCK=${LI_LOCK:-/tmp/living-icon-loop.v2.lock}
PIDF=${LI_PIDFILE:-/tmp/living-icon-loop.pid}
exec 9>"$LOCK"
flock -n 9 || { echo "living-icon-loop already running" >&2; exit 1; }
cd "${LI_DIR:-/workspace/living-icon-repo}" || exit 1
L=${LI_LOGS:-/workspace/agent-backups/Eve/logs}
DERIVE=${LI_DERIVE:-python3 scripts/derive_eve_state.py --once}
SYNC=${LI_SYNC:-python3 scripts/sync_live_moods.py}
REFRESH=${LI_REFRESH:-python3 docs/dashboard/refresh_data.py}
SLEEP=${LI_SLEEP:-5}
cleanup() { [ "$(cat "$PIDF" 2>/dev/null)" = "$$" ] && rm -f "$PIDF"; exit 0; }
trap cleanup INT TERM EXIT
rotate() { for f in "$L"/*.log; do [ -f "$f" ] || continue
  if [ $(stat -c %s "$f") -gt 5242880 ]; then tail -c 1048576 "$f" > "$f.tmp" && mv "$f.tmp" "$f"; fi; done; }
i=0
while true; do
  echo $$ > "$PIDF"   # rewritten each tick (survives an old copy's exit trap)
  if [ $((i % 120)) -eq 0 ]; then bash -c "$REFRESH" >> "$L/refresh.log" 2>&1; rotate; fi
  bash -c "$DERIVE" >> "$L/deriver.log" 2>&1
  bash -c "$SYNC" >> "$L/sync-moods.log" 2>&1
  i=$((i+1))
  [ -n "$LI_MAX_TICKS" ] && [ $i -ge $LI_MAX_TICKS ] && break
  sleep "$SLEEP"
done
