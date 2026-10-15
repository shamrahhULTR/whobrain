#!/bin/bash
# Keep BRAIN running all the time, whether or not Claude, the app, or a browser is open.
#
#   brain/always-on.sh install     start now, start at every login, restart if it ever dies
#   brain/always-on.sh status      is it up
#   brain/always-on.sh restart     pick up code changes
#   brain/always-on.sh uninstall   remove the login service
#
# Uses a per-user macOS LaunchAgent. No admin password, no root.

set -euo pipefail

LABEL="${BRAIN_LABEL:-com.whobrain.hub}"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT="${BRAIN_PORT:-4747}"
DOMAIN="gui/$(id -u)"
LOGS="$HERE/.logs"

write_plist() {
  mkdir -p "$HOME/Library/LaunchAgents" "$LOGS"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$HERE/serve.py</string>
  </array>
  <key>WorkingDirectory</key><string>$HERE</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>BRAIN_PORT</key><string>$PORT</string>
    <key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>5</integer>
  <key>ProcessType</key><string>Interactive</string>
  <key>StandardOutPath</key><string>$LOGS/brain.log</string>
  <key>StandardErrorPath</key><string>$LOGS/brain.log</string>
</dict>
</plist>
EOF
}

is_loaded() { launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; }

wait_up() {
  for _ in $(seq 1 30); do
    curl -fs --max-time 1 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1 && return 0
    sleep 0.3
  done
  return 1
}

case "${1:-status}" in
  install)
    if lsof -iTCP:"$PORT" -sTCP:LISTEN -n -P >/dev/null 2>&1 && ! is_loaded; then
      echo "Port $PORT is already in use by another process. Stop it first, then rerun." >&2
      lsof -iTCP:"$PORT" -sTCP:LISTEN -n -P >&2
      exit 1
    fi
    write_plist
    if is_loaded; then launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true; fi
    launchctl bootstrap "$DOMAIN" "$PLIST"
    launchctl enable "$DOMAIN/$LABEL"
    if wait_up; then echo "BRAIN is live and permanent: http://localhost:$PORT"
    else echo "Installed, but not answering yet. See $LOGS/brain.log" >&2; exit 1; fi
    ;;
  restart)
    is_loaded || { echo "Not installed. Run: $0 install" >&2; exit 1; }
    launchctl kickstart -k "$DOMAIN/$LABEL"
    if wait_up; then echo "restarted"; else echo "not answering, see $LOGS/brain.log" >&2; exit 1; fi
    ;;
  uninstall)
    if is_loaded; then launchctl bootout "$DOMAIN/$LABEL" || true; fi
    rm -f "$PLIST"
    echo "removed"
    ;;
  status)
    if is_loaded; then echo "service: installed ($LABEL)"; else echo "service: NOT installed"; fi
    if curl -fs --max-time 2 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
      echo "hub:     answering on http://localhost:$PORT"
    else
      echo "hub:     NOT answering"
    fi
    ;;
  *) echo "usage: $0 {install|status|restart|uninstall}" >&2; exit 2 ;;
esac
