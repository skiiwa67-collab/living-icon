#!/bin/bash
# Living Icon loop (Chris-approved exception; same loop, no cron). Box-local only.
#  - singleton: flock on /tmp/living-icon-loop.lock (+ pidfile); a second copy exits at once
#  - supervises exactly one Eve deriver (restarted if it dies; killed on loop exit)
#  - every 5 s: sync_live_moods.py (mirror each bot's own file -> docs/status/live, hold expiry, OK overlay)
#  - every 600 s: refresh_data.py (data.json + both feed.json, atomic)
#  - logs > 5 MB are truncated to their last 1 MB
exec 9>/tmp/living-icon-loop.lock
flock -n 9 || { echo "living-icon-loop already running" >&2; exit 1; }
echo $$ > /tmp/living-icon-loop.pid
cd /workspace/living-icon-repo
L=/workspace/agent-backups/Eve/logs
DPID=
start_deriver() {
  pkill -f 'scripts/derive_eve_state.py --loop' 2>/dev/null; sleep 0.5
  python3 scripts/derive_eve_state.py --loop 5 >> $L/deriver.log 2>&1 &
  DPID=$!; echo $DPID > /tmp/living-icon-deriver.pid
}
cleanup() { [ -n "$DPID" ] && kill $DPID 2>/dev/null; rm -f /tmp/living-icon-loop.pid /tmp/living-icon-deriver.pid; exit 0; }
trap cleanup INT TERM EXIT
rotate() { for f in $L/*.log; do [ -f "$f" ] || continue
  if [ $(stat -c %s "$f") -gt 5242880 ]; then tail -c 1048576 "$f" > "$f.tmp" && mv "$f.tmp" "$f"; fi; done; }
start_deriver
i=0
while true; do
  kill -0 $DPID 2>/dev/null || { echo "$(date -Is) deriver died; restarting" >> $L/deriver.log; start_deriver; }
  if [ $((i % 120)) -eq 0 ]; then python3 docs/dashboard/refresh_data.py >> $L/refresh.log 2>&1; rotate; fi
  python3 scripts/sync_live_moods.py >> $L/sync-moods.log 2>&1
  i=$((i+1)); sleep 5
done
