#!/bin/sh
echo "[return] SpotUI exit requested; rebooting" > /tmp/return_to_hiby.log
for pid in $(ps | grep -E "[s]potui-ui-poc|[s]potui_daemon|[l]ibrespot|[a]play|[s]tart_spotui" | awk "{print \$1}"); do
    kill "$pid" 2>/dev/null
done
sync
sleep 1
reboot
