## Summary

Describe the smallest user-visible or technical change in this pull request.

## Related issue

Link the agreed issue or change proposal. Write `Small documentation fix` only
when prior agreement was not required.

## Scope and risk

- Files and components changed:
- Behavior intentionally unchanged:
- Playback, protocol, audio, launcher, firmware, storage, or recovery risks:

## Validation

- [ ] I ran `git diff --check`.
- [ ] I inspected the complete relevant diff.
- [ ] I did not run repository-wide `cargo fmt`.
- [ ] I built every affected binary with the documented target commands, or
      explained why no build applies below.
- [ ] I verified affected binary type and hashes, when applicable.
- [ ] I documented physical-device testing, or clearly state that this change
      has not been tested on a device.

Commands and results:

```text
Replace with concise validation output.
```

## Device testing

- Device and firmware revision:
- SpotUI version/source commit:
- Output tested:
- Test cases and results:
- Not tested:

## Safety and privacy

- [ ] This pull request contains no credentials, tokens, WiFi configuration,
      cache files, private logs, firmware images, proprietary binaries, device
      backups, or compiled SpotUI binaries.
- [ ] UI/daemon protocol changes update and deploy both sides as a compatible
      pair.
- [ ] Daemon changes were made in the canonical repository source and copied
      into the librespot tree only for building.
- [ ] The change preserves rollback safety and the latest-tap-wins behavior
      where applicable.

## Maintainer notes

SpotUI is maintained with limited time and physical hardware. Submission does
not guarantee review, merge, or a release schedule, and a different
implementation may be preferred after device testing.
