#!/bin/sh

# Failsafe cleanup function
cleanup() {
    [ -n "$DAEMON_PID" ] && kill -9 "$DAEMON_PID" 2>/dev/null
    killall spotui_daemon 2>/dev/null
    killall -CONT hiby_player 2>/dev/null
}

# Catch any exit, crash, or interrupt and run the cleanup function
trap cleanup EXIT INT TERM

# 1. Suspend the stock OS
killall -STOP hiby_player 2>/dev/null

# 2. Start daemon in the background
/usr/data/ld-musl-mipsel-sf.so.1 \
    /usr/data/spotui_daemon \
    -c /usr/data/librespot-cache > /tmp/spotui.log 2>&1 &
DAEMON_PID=$!

# Give the daemon 1 second to connect
sleep 1

# 3. Start SpotUI UI in the foreground
/usr/data/ld-musl-mipsel-sf.so.1 \
    /usr/data/spotui-ui-poc
