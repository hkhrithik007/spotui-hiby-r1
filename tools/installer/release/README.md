# SpotUI 0.1.0-beta.2 tester bundle

This is an early tester package for the **HiBy R3 Pro II only**. It combines
the device-tested SpotUI runtime with a firmware image derived from HiBy Mods
v1.5 and a Linux desktop helper for private Spotify authorization.

The firmware base and its licensing boundary are documented by the upstream
HiBy Mods [v1.5 release](https://github.com/hiby-modding/hiby-mods/releases/tag/v1.5),
[license](https://github.com/hiby-modding/hiby-mods/blob/main/LICENSE), and
[firmware notice](https://github.com/hiby-modding/hiby-mods/blob/main/NOTICE.md).

Read `PRIVACY.md`, `DISCLAIMER.md`, `HIBY-MODS-NOTICE.md`, and
`docs/recovery.md` before flashing. Custom firmware can leave the device
temporarily unbootable. Keep official recovery firmware for the exact HiBy R3
Pro II available.

The detailed maintainer validation and retired-image record is in
`docs/tester-installer.md`.

## Requirements

- HiBy R3 Pro II, charged before flashing;
- reliable microSD card;
- Spotify Premium account;
- x86-64 Linux computer with Python 3 and ADB;
- USB cable and a browser on the same computer;
- willingness to recover the device with Volume Up + Power if necessary.

Do not use this package on another model.

## 1. Verify the bundle

From the extracted directory:

```fish
sha256sum -c SHA256SUMS
```

Every entry must report `OK`. Stop if any hash differs.

## 2. Flash and provision SpotUI

1. Copy `r3proii.upt` and `spotui-runtime.tar.xz` to the SD-card root.
2. Safely eject the SD card and insert it into the powered-off player.
3. Hold Volume Up and press Power to enter the firmware updater.
4. Wait for the updater to report success and allow the player to boot.
5. Leave the SD card inserted through the first stock HiBy boot so the guarded
   background provisioner can validate and install the runtime.
6. After the stock interface appears, wait at least 60 seconds before enabling
   ADB or launching SpotUI. Initial extraction begins after a 30-second
   startup-I/O settling window and retries safely in the background.

The tested firmware reached the stock HiBy interface in about 10 seconds. The
provisioner runs after the stock player starts and never packages account or
WiFi data. A failed extraction attempt removes its staging directory and
retries without blocking the stock interface or activating partial files.

## 3. Authorize Spotify privately

1. In the stock interface, open Settings → About.
2. Tap About ten times to enable ADB, then connect USB.
3. Confirm `adb devices` shows exactly one device in the `device` state.
4. Keep SpotUI closed and run:

```fish
python3 onboard_spotify.py
```

The helper opens Spotify's authorization page. It never requests a password.
After approval, it installs only the reusable librespot credential on your
player, retains one private rollback copy there, and removes the temporary
computer copy. See `docs/credential-onboarding.md` for details and rollback.

## 4. Launch and test

Tap the SpotUI tile once. On a fresh boot, the audio-safety readiness gate may
wait until roughly 60 seconds of device uptime before taking over the display.
Repeated taps are ignored while launch is already pending.

Confirm:

- Liked Songs loads;
- a track plays through the intended headphone output;
- pause/resume and Next work;
- a searched track plays;
- Exit → Confirm returns through a normal reboot.

ADB must be enabled again after a reboot when diagnostics are needed. Normal
SpotUI playback does not require the computer after authorization.

## Recovery

If SpotUI authentication fails, use the documented credential rollback before
changing firmware. If the device does not boot, use official recovery firmware
for the exact HiBy R3 Pro II with the Volume Up + Power updater procedure.
Read `docs/recovery.md` completely before attempting recovery.

Do not upload device logs, credentials, WiFi configuration, cache directories,
or backups to an issue. Use the repository's privacy-safe issue templates.
