# Roadmap

SpotUI is currently a `0.1.0-beta.1` developer beta source release for the
HiBy R3 Pro II. This roadmap is intentionally conservative: stability,
documentation, and recovery come before convenience features.

## Current status

- Developer beta with a source-only public repository.
- Tested primarily on the HiBy R3 Pro II.
- No ready-to-flash firmware builds are provided in this repository.
- Manual build, patching, and device setup are still required.
- The current UI is designed around large, simple touch rows for reliable use on the device screen.

## Recently completed

- Added queued playback for Liked Songs, playlists, and search results.
- Added latest-tap-wins track selection and responsive, tap-safe Search.
- Added persistent recent-search history with newest-first ordering,
  deduplication, one-tap reruns, and clear-history control.
- Added queue-aware Previous, Next, and Up Next controls.
- Added a dedicated Now Playing screen with larger metadata, elapsed and
  remaining time, seeking, playback controls, and direct queue access.
- Expanded Now Playing with themed track artwork, queue and playback-mode
  context, output status, larger controls, and clearer time information.
- Preserved the active queue and retried the current track after a first
  transient Spotify unavailable event.
- Added persistent shuffle and repeat modes.
- Added touchscreen seeking and hardware volume feedback.
- Added ten redesigned themes with adaptive ambient motion.
- Added a staged startup status screen and supervised daemon recovery.
- Added automatic search-result invalidation and refresh after a supervised
  daemon restart, preventing stale result queues from remaining tappable.
- Added elapsed startup timing and stage-specific Wi-Fi, Spotify, and library
  retry controls.
- Added live WiFi, Spotify, audio, output, and queue diagnostics.
- Added an on-device `0.1.0-beta.1` version identifier in Diagnostics.
- Added persistent 30-second, 60-second, 2-minute, 5-minute, and Never
  screen-sleep settings with safe touch and power-button wake while audio
  continues.
- Tested early stock-side launch feedback and retained the manual, audio-safe
  handoff after framebuffer contention made the prototype unsuitable.
- Verified cold-start playback and automatic 3.5 mm/4.4 mm routing.
- Added a guarded local firmware builder with pre-build and packaged-image integrity checks.
- Documented the verified local firmware build workflow.
- Added final stock-matched SpotUI launcher artwork for both HiBy themes.
- Changed the visible Qobuz launcher caption to SpotUI while preserving internal widget and localization keys.
- Verified early-launch readiness, SpotUI startup, and audio playback on-device.
- Added persistent brightness settings across SpotUI launches.
- Documented the tested UI and daemon cross-build and deployment workflow.
- Expanded recovery, rollback, and common failure troubleshooting procedures.
- Added a developer beta installation guide with prerequisites, validation,
  limitations, and rollback guidance.
- Added and device-tested a guarded two-file HMOD v1.5 installer builder with
  low-memory runtime extraction, exact-input validation, and safe repeat-boot
  behavior.
- Added and device-tested private desktop OAuth onboarding with atomic ADB
  credential installation, strict permissions, and device-local rollback.
- Completed a full release-candidate regression covering all playback sources,
  rapid selection, automatic advancement, controls, search recovery,
  sleep/wake, headphone reconnection, UI-only restart, full reboot, settings
  persistence, themes, menus, Now Playing, Up Next, and Diagnostics.

## Current development priorities

- Continue small, device-tested playback and navigation improvements.
- Keep public setup, recovery, and feature documentation synchronized with
  tested milestones.
- Preserve and publish verifiable release-candidate hashes without adding
  credentials, proprietary firmware, or user-specific device files.

## Next planned improvements

### Library and navigation polish

- Add a compact page or position indicator for long Liked Songs, playlist,
  Search, and Up Next lists.
- Review return paths and per-view browsing position so moving through Search,
  playlists, Now Playing, and the library preserves useful context.
- Make the difference between the active playback queue and the currently
  browsed source clearer without shrinking touch targets.

### Diagnostics and recovery clarity

- Distinguish network, Spotify-session, daemon-restart, and audio-output
  recovery states more clearly in Diagnostics and logs.
- Record concise, privacy-safe troubleshooting steps that users can include in
  issue reports without exposing account or network credentials.
- Continue targeted recovery tests when a real, reproducible failure is found,
  while preserving the current simple supervised design.

### Installation and release safety

- Add host and device preflight checks for model, storage, expected files,
  binary architecture, and rollback readiness.
- Define a compatibility matrix as additional firmware revisions or devices
  are tested by owners.
- Explore a patch-only workflow based on a user-supplied stock image, without
  redistributing proprietary firmware.

### Platform integration research

- Profile the HiBy_OS handoff and investigate a faster path from tapping the
  launcher tile to seeing SpotUI, without bypassing the codec and mixer
  readiness checks that protect headphone audio.
- Investigate deeper stock-side launch feedback or integration that remains
  responsive while the safe handoff is pending.
- Design and validate a fully dedicated SpotUI launcher icon and identity in
  place of the current Qobuz-derived SpotUI integration.
- Evaluate Bluetooth audio-output support, including pairing assumptions,
  routing, reconnection, status reporting, and playback behavior.
- Investigate whether HiBy MSEB tuning can be exposed safely inside SpotUI,
  including control discovery, persistent settings, output compatibility, and
  coexistence with the stock player's audio configuration.

## Possible future goals

- Support additional HiBy models if tested by device owners.
- Improve UI polish while keeping the interface readable and touch-friendly.
- Continue strengthening recovery behavior for reproducible backend failures.
- Evaluate optional album artwork only if a bounded prototype meets the
  device's memory, network, and framebuffer-performance limits.
- Consider optional bring-your-own-client-ID OAuth support for library writes,
  without making it a standard installation requirement.

## Current service limitation

SpotUI's librespot playback authentication can read the user's Liked Songs but
cannot request Spotify's separate `user-library-modify` Web API permission.
Like and unlike controls are therefore intentionally not included. A future
implementation would require a separate OAuth flow and user-supplied Spotify
developer application configuration.

## Launcher limitation

The stock HiBy player must finish initializing the codec and mixer before
SpotUI takes over. A cold manual launch can therefore leave the stock interface
visible for tens of seconds before SpotUI's own loading page appears. The
nonblocking launcher accepts the request once and ignores repeated taps while
it waits.

A tested framebuffer-only preparation page was not retained: the proprietary
stock interface continuously flips and redraws its framebuffer pages, causing
the two interfaces to flicker and leaving stale frames visible. Refreshing the
prototype aggressively enough to dominate the display would add load during
the audio-critical initialization period. A clean stock-side status dialog
would require deeper, firmware-specific integration with the proprietary HiBy
interface.

SpotUI also does not take over automatically after every reboot. Automatic
takeover would interrupt users who intend to use the stock player, so manual
launching remains the deliberate default.

## Not planned right now

- One-click installer.
- Ready-to-flash firmware builds in this repository.
- Paid or paywalled features.
- Guaranteed device support.
- Support for devices that have not been tested by owners.

## Contribution priorities

Helpful contributions include:

- Testing on the HiBy R3 Pro II.
- Careful reports from other HiBy models.
- Documentation improvements.
- Recovery notes.
- Build reproducibility improvements.
- Small, readable UI improvements that do not reduce touch target size.
