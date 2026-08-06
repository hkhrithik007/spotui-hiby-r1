# HMOD v1.5 tester installer

> [!CAUTION]
> This installer and its output remain experimental. Public testers should use
> only the exact archive attached to a clearly marked SpotUI GitHub prerelease,
> verify its published outer SHA-256 and bundled `SHA256SUMS`, and read the
> included recovery guidance before flashing. Locally rebuilt output must not
> be distributed until it completes the same review and device-validation gate.

The tester installer converts the exact published HiBy Mods v1.5 firmware for
the HiBy R3 Pro II into a two-file SpotUI beta installer. Testers copy the
firmware and its matched runtime archive to the SD card. The builder does not
download firmware, flash a device, or include Spotify credentials, WiFi
configuration, cache contents, or device-specific files.

## Supported firmware input

Only this upstream image is accepted:

```text
Project:  hiby-modding/hiby-mods
Release:  v1.5
Filename: r3proii-v1.5-hmod.upt
SHA-256:  631af685977877f65288e371d49f3b2839681ee4ca4713234f498519e2ab33f2
Device:   HiBy R3 Pro II
```

The builder checks the complete firmware, rootfs, kernel, player, player
wrapper, backup player, and localization hashes. It refuses similar or
modified inputs.

HiBy Mods tooling, documentation, and original project assets have their own
license. The firmware contains proprietary HiBy components that are not
covered by that MIT license. Preserve the upstream license, firmware notice,
credit, and warranty language when preparing any SpotUI release.

## What the installer adds

The generated image:

- preserves the verified HMOD v1.5 kernel and player modifications;
- applies only the reviewed 79-byte SpotUI launcher delta to `hiby_player`;
- signals a prestarted lightweight broker without forking the stock player;
- retains the original backup player;
- prevents the stock wrapper from rebooting during an intentional SpotUI
  launcher handoff;
- changes the visible Qobuz tile artwork and caption to SpotUI;
- emits a separate compressed, private-data-free SpotUI runtime archive;
- stores only the runtime hashes, size, and version in the firmware rootfs;
- starts the stock player before launching a low-priority background
  provisioner;
- provisions the SD-card runtime archive into `/usr/data` without blocking
  boot;
- retains manual launch through the repurposed Qobuz tile;
- does not enable SpotUI autostart or force always-on ADB.

The provisioner installs only when all six runtime targets are absent. If
existing files are complete and match the release manifest, it leaves them in
place. If an existing runtime is incomplete or differs, it refuses to
overwrite anything. SD waiting, hashing, and extraction happen in a
low-priority background worker after `hiby_player` starts. The worker records
its result in:

```text
/tmp/spotui-provision.log
```

## Build inputs

The builder requires locally reviewed release binaries:

- `spotui-ui-poc`;
- `spotui_daemon`;
- `ld-musl-mipsel-sf.so.1`.

The builder verifies that the UI and daemon are 32-bit little-endian MIPS PIE
executables using the expected musl interpreter. It follows a loader symlink
and packages the actual loader file.

From the SpotUI repository, a Fish-compatible invocation is:

```fish
tools/installer/build_spotui_tester_upt.sh \
    --base /path/to/r3proii-v1.5-hmod.upt \
    --ui engine/ui/target/mipsel-unknown-linux-musl/release/spotui-ui-poc \
    --daemon /path/to/librespot/target/mipsel-unknown-linux-musl/release/examples/spotui_daemon \
    --loader /path/to/ld-musl-mipsel-sf.so.1 \
    --output /path/to/r3proii-hmod-1.5-spotui-0.1.0-beta.1.upt \
    --runtime-output /path/to/spotui-runtime.tar.xz
```

Neither output path may already exist. The builder:

1. verifies and extracts HMOD v1.5;
2. patches only the known player, wrapper, labels, and launcher artwork;
3. builds a reproducible compressed runtime archive for the SD card;
4. adds only its verified metadata and the guarded background provisioner to
   the firmware;
5. rebuilds the LZO SquashFS within the root partition limit;
6. regenerates the OTA chunk chain and manifest;
7. packages the `.upt`;
8. re-extracts the result and verifies every critical hash;
9. confirms that the kernel is unchanged and prints release checksums.

The runtime uses an explicit XZ preset-4 dictionary and CRC32 checksum. The
device has no swap and only about 56 MB of RAM; desktop-oriented XZ preset 9
requires too much decompression memory for its BusyBox decoder.

Generated `.upt` images, runtime archives, and runtime binaries must not be
committed to the Git-tracked source tree. An exact, device-tested
firmware/runtime pair may instead be attached to a clearly marked GitHub
prerelease with its hashes, provenance, notices, and recovery warning.

## Maintainer device-validation record

The following unpublished pair completed the controlled test sequence on one
HiBy R3 Pro II on 2026-07-27:

```text
Firmware SHA-256: 7dd7dc29b165e579f17199d0435d4666b9e689fedd3b19a581fec9f99ba0213c
Firmware MD5:     1381cae3dd08567ce649889b09e2a91d
Runtime SHA-256:  38c48bf1896838d836e082e9c67901ad5a8bc484aa268cbfd8ece79414015364
Rootfs SHA-256:   09e99ee33bc6237a23a0a8179ee406d52f1fd0ea3149dfbd8f4444647f6b2da4
Rootfs size:      37322752 bytes
Runtime profile:  XZ preset 4, CRC32, 4 MiB dictionary
```

Stage 1 preserved an existing matching SpotUI runtime, reached the stock HiBy
interface in about 10 seconds, launched SpotUI, and passed playback, controls,
queue, search, sleep/wake, and exit/reboot testing. Stage 2 installed the same
runtime from an SD card after all six runtime targets were absent. Every
installed hash and permission matched the packaged manifest. Rapid taps still
coalesced to the newest request, search playback remained correct, audio used
the expected `aplay` subprocess, and the exit path rebooted in about 10
seconds. The following boot detected matching installed metadata and skipped
extraction without leaving a staging directory or lock.

This record establishes the known-good maintainer build; it is not by itself
authorization to publish the artifacts. Public testing still requires the
credential onboarding, release packaging, notices, and recovery guidance
described in this document.

## Privacy-remapped release-candidate validation

The public-tester candidate was rebuilt with neutral Rust source paths and a
bounded background extraction settling/retry policy. The following exact pair
completed both existing-runtime and fresh-provision testing on the maintainer
device on 2026-07-27:

```text
Firmware SHA-256: b4e78ab3eb7154f68ffc333a9fdd3770de5e16b1a65752a908812e3c7cfe6df0
Firmware MD5:     1a9afde2f694c11ae12ad9f9e7e70ca4
Runtime SHA-256:  f16ff95b69400ee360e27c860e690835e3bea8898742dd65b3b362048d0e8da8
Rootfs SHA-256:   c5448b6716d71702ec810988572d24fba1eb3c319b22cbefd6903f8af6dd06f1
Rootfs size:      37322752 bytes
UI SHA-256:       e8111b160f8daad4bf2ebae94beaba5fe0f67ad29a5e4596334c4789e4bb573e
Daemon SHA-256:   f7e8cbcedbb918900cf85aa7a4589c18ec4a9031db6754ac915f13daf00c7769
Runtime profile:  XZ preset 4, CRC32, 4 MiB dictionary
```

The stock interface appeared in approximately 5–10 seconds and was not
blocked by provisioning. With all six runtime targets absent, the final
firmware waited 30 seconds for startup I/O to settle and installed the runtime
on its first extraction attempt. Every installed hash and permission matched,
metadata matched the firmware manifest, no staging directory or lock remained,
and private device credentials retained mode 0600 inside a mode-0700 cache.
Liked Songs, Search, pause/resume, Next, audio, highlighting, and metadata then
passed on the freshly provisioned runtime.

Two intermediate privacy-remapped firmware images are retired because their
fresh-boot extraction windows were too short. Do not distribute images with
these SHA-256 values:

```text
28de738dc6aee77e1298b160876f011b62949adafcac6d524c670bd515af49b7
46ef2c45add56850f48640e83cb6b0b9f72f8de5803287878d45a97f7fa7fa25
```

Both failed safely without activating partial runtime files or changing
credentials. The final candidate supersedes them.

## Retired embedded-payload prototype

The first unpublished prototype embedded the compressed runtime in the rootfs
and ran its verifier synchronously before `hiby_player`. Its updater reported
success, but the tested R3 Pro II remained at the HiBy boot logo. The device
was recovered with the preserved working firmware and all persistent SpotUI
data remained intact.

The failed prototype has SHA-256:

```text
9c3f551d0567ea31dda8bc6a0efffea1d3b662c69417aeaba7154088c8eba758
```

Do not flash, distribute, or use that image as a future build base. The
two-file design intentionally keeps the multi-megabyte runtime out of the
rootfs and makes provisioning unable to delay the stock UI boot path.

An intermediate two-file build booted normally but its fresh-install worker
rejected the valid runtime archive as corrupt because that archive used the
64 MiB XZ preset-9 dictionary. It failed before creating any partial runtime
files. The incompatible runtime archive has SHA-256:

```text
e5b6a25dc196679298aceecaf47638b9d870c6c5cd898a225c01b1184501a1cc
```

Do not distribute that archive or either firmware/runtime pair built around
it. The builder now fixes the archive to the device-tested low-memory profile.

## Authentication boundary

The image intentionally contains no account data. A new tester enables ADB
from the stock HMOD interface and runs the separately built desktop OAuth
helper before launching SpotUI. The tested helper creates the reusable
librespot credential in a private temporary directory, stages and verifies it
over ADB, preserves one device-local rollback copy, and removes the temporary
host copy. See [Spotify credential onboarding](credential-onboarding.md).

Authentication onboarding passed its complete device test on 2026-07-27. It
does not make the firmware or runtime archive account-specific, configure
WiFi, or enable ADB permanently.

## Controlled device-test sequence

### Stage 1: existing matching runtime

1. Pause playback and confirm `aplay` has exited.
2. Archive the active UI, daemon, loader, three launcher scripts, and their
   hashes on the laptop.
3. Record the active firmware, player, rootfs, kernel, and `/usr/data` hashes.
4. Keep official stock recovery firmware for the exact R3 Pro II available.
5. Copy the verified firmware to the SD card as `r3proii.upt` and its matched
   runtime archive as `spotui-runtime.tar.xz`.
6. Flash it with the normal R3 Pro II firmware update procedure.
7. Let the device boot into the stock HiBy interface; do not launch SpotUI yet.
8. Enable ADB manually from HMOD's About screen.
9. Confirm that the stock UI appears before provisioning work and that
   `/tmp/spotui-provision.log` reports the runtime already matches the
   packaged version.
10. Verify the active runtime, player, kernel, installer, and payload hashes.
11. Launch SpotUI and run the complete beta regression.
12. Exit SpotUI and confirm the normal reboot path.

### Stage 2: fresh provisioning

Perform this only after Stage 1 passes and the active runtime has a verified
laptop archive.

1. Pause playback and archive the active runtime again.
2. Remove the six active runtime targets only through a separately reviewed
   ADB command; do not remove credentials, WiFi configuration, or unrelated
   `/usr/data` content.
3. Keep the matched `spotui-runtime.tar.xz` at the SD root and reboot so the
   background provisioner installs it after the stock player starts.
4. Verify the provision log, permissions, version marker, and every installed
   hash before launching SpotUI.
5. Run the full cold-launch, playback, queue, search, controls, sleep/wake,
   headphone, persistence, exit, and recovery regression.

Do not publish the image if either stage requires an unexplained manual repair.
