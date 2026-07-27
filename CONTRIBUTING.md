# Contributing to SpotUI

SpotUI welcomes focused contributions, device-test reports, and documentation
improvements. The project is maintained by one person with limited time and
access to one primary test device, so opening an issue or pull request does not
guarantee a response, review, merge, or release schedule.

The maintainer retains final authority over project scope, implementation,
testing requirements, and releases. Do not request direct repository access;
contributions should use a fork and pull request.

## Good contributions for the current beta

- Reproducible HiBy R3 Pro II test reports
- Corrections and improvements to public documentation
- Small, focused UI or reliability fixes
- Privacy-safe diagnostic improvements
- Build reproducibility and recovery improvements
- Carefully scoped work that already has maintainer agreement

## Open an issue before substantial work

Use the change-proposal form and wait for maintainer agreement before starting
work involving:

- playback, queues, latest-tap behavior, or the UI/daemon wire protocol;
- daemon lifecycle, librespot, audio buffering, ALSA, or output routing;
- launcher, framebuffer, touchscreen, power, sleep, or firmware integration;
- Bluetooth, MSEB, new device support, or stock-player interaction;
- authentication, library writes, credentials, or network configuration;
- large refactors, new dependencies, generated code, or architecture changes.

Silence does not mean that a proposal is approved. Unsolicited substantial
pull requests may be closed without detailed review because validating them
can require risky firmware work and extended testing on physical hardware.

## Changes that will not be accepted

- Proprietary firmware, extracted proprietary binaries, or modified `.upt`
  images
- Spotify credentials, tokens, cache files, WiFi configuration, private logs,
  or device backups
- Compiled SpotUI binaries committed to the source repository
- Broad formatting-only changes, including repository-wide `cargo fmt`
- Large unrelated changes combined in one pull request
- Claims of compatibility with hardware that was not actually tested
- Changes that weaken rollback, device-storage, or credential safety

## Development workflow

1. Read `AGENTS.md`, the build guide, recovery notes, and relevant source before
   changing anything.
2. Create a focused branch in your fork.
3. Make one controlled change and avoid unrelated cleanup.
4. Run `git diff --check` and inspect the complete diff.
5. Build every affected binary with the documented MIPS target commands.
6. Verify output type and hashes.
7. Report device testing honestly. If no physical-device test was performed,
   say so clearly.
8. Open a pull request using the repository template and link the agreed issue
   when one is required.

Never run `cargo fmt` across the existing large Rust files. Keep playback
control sends fire-and-forget, treat the UI and daemon protocol as a matched
interface, and preserve latest-tap-wins behavior. The complete technical rules
are in `AGENTS.md`.

## Device-test expectations

Playback or queue changes normally require testing of:

- normal and rapid taps in Liked Songs and playlists;
- Search playback and source-aware highlighting;
- automatic advancement and final queue completion;
- Previous, Next, pause, resume, and seeking;
- switching among Liked Songs, playlists, and Search;
- screen sleep/wake and the applicable headphone output;
- UI-only restart when relevant and a full device reboot.

Use [the beta testing guide](docs/testing.md) for report details.

## Review expectations

- Reviews are performed when maintainer capacity allows; there is no service
  level or response deadline.
- Pull requests may be closed when they are out of scope, unsafe, inactive, or
  too large to validate on the available hardware.
- Maintainer edits or a different implementation may be preferred even when a
  proposal is useful.
- Code is not merged solely because it builds; device behavior and recovery
  risk matter.

By submitting a contribution, you agree that it may be distributed under the
repository's MIT License.

For sensitive reports, follow `SECURITY.md` and never post secrets publicly.
