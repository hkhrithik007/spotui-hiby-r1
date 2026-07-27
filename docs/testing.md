# Beta testing SpotUI

SpotUI testing is currently limited to experienced HiBy R3 Pro II owners who
already have a working development installation and a recovery path. This
guide does not make SpotUI generally installable and must not be used as a
substitute for the developer installation, build, or recovery documents.

## Before testing

- Confirm that the device is exactly a HiBy R3 Pro II.
- Keep official stock recovery firmware available.
- Confirm ADB access and back up every replaced device file.
- Read the developer installation and recovery documents completely.
- Use the source and version named in the test request.
- Never publish credentials, WiFi details, cache files, private account logs,
  proprietary firmware, or device backups.

Do not test experimental builds on another HiBy model unless the maintainer
has explicitly agreed to a separate hardware investigation.

## Information to record

- SpotUI version shown in Diagnostics
- Source commit or tag
- Exact device model and firmware revision
- Installation path used
- 3.5 mm, 4.4 mm, or other output under test
- Screen-sleep, theme, shuffle, and repeat settings
- Whether the test started after a full reboot
- Clear reproduction steps and the observed result

## Core beta test

1. Reboot the device and confirm that the stock HiBy interface is responsive.
2. Launch SpotUI once and record the visible startup stages and timing.
3. Confirm the Diagnostics version and status tiles.
4. Play several Liked tracks and listen for startup delay or stutter.
5. Rapidly select several Liked tracks and confirm only the final track plays.
6. Repeat normal and rapid selection in a playlist.
7. Run a new Search and play a result.
8. Test Previous, Next, pause, resume, seeking, Now Playing, and Up Next.
9. Confirm automatic advancement and synchronized highlighting and metadata.
10. Test the configured screen sleep and physical power-button wake while
    audio is playing.
11. Test the applicable headphone-removal and reconnection behavior.
12. Confirm settings persist after a full reboot.
13. Exit SpotUI normally and confirm the device returns through its expected
    reboot path.

Only perform failure-injection, daemon-restart, firmware, launcher, Bluetooth,
or MSEB tests when the maintainer has agreed to the exact procedure.

## Logs and privacy

The primary runtime logs are:

```text
/tmp/start_spotui.wrapper.log
/tmp/spotui-ui.log
/tmp/daemon.log
```

Inspect and sanitize logs before sharing them. Remove account names, network
information, credentials, tokens, and any unrelated personal data. Prefer the
smallest log excerpt that shows the failure.

Pause playback before hashing, pulling, or copying large device binaries.
Maintenance I/O can compete with real-time audio and create test-only
underruns.

## Reporting results

Use the repository's **Beta test report** issue form for a passing or mixed
test session. Use **Bug report** for one reproducible defect. Use **Change
proposal** before starting substantial implementation work.

Maintainer capacity is limited. A complete report may not receive an immediate
response, but structured results are still valuable for future triage.
