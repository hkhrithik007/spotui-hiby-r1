# Tester release bundle workflow

The tester release bundle combines the exact device-tested firmware/runtime
pair with the private OAuth onboarding tools and required notices. It is a
local build artifact, not a source-tree asset. Do not upload it until every
privacy, checksum, extraction, recovery, and device test passes.

## Build the privacy-remapped host helper

Do not package the ordinary Cargo output directly: Rust dependencies may embed
the build user's absolute filesystem paths. Use the guarded builder:

```fish
tools/auth-helper/build_release.sh \
    --output /private/output/spotui-auth-helper
```

The builder uses the locked dependency graph, remaps local home/build
paths, rejects any remaining local path or embedded private-key material, and
prints the resulting SHA-256.

The MIPS UI and daemon must also be rebuilt with neutral source paths before
packaging. Use the normal repository build commands with these release flags:

```fish
env RUSTFLAGS='--remap-path-prefix=/home=/build/source' \
    cargo +nightly build \
    --release \
    -Z build-std=std,panic_abort \
    --target mipsel-unknown-linux-musl

env RUSTFLAGS='-C strip=symbols --remap-path-prefix=/home=/build/source' \
    cargo +nightly build \
    --release \
    --example spotui_daemon \
    -Z build-std=std,panic_abort \
    --target mipsel-unknown-linux-musl \
    --no-default-features \
    --features 'rustls-tls-webpki-roots,with-libmdns'
```

Run the first command from `engine/ui` and the second from the verified
librespot 0.8.0 build tree after refreshing and hash-checking the canonical
daemon source copy. The privacy audit rejects ordinary binaries that retain a
maintainer home path.

## Build the bundle

Use only the archived known-good firmware/runtime pair. Pass any private value
that must be forbidden from the output with a separate `--private-marker`
argument. Marker values are scanned but are never copied into reports or the
bundle.

```fish
tools/installer/build_tester_release_bundle.sh \
    --firmware /private/artifacts/r3proii-spotui-tested.upt \
    --hmod-base /private/artifacts/r3proii-v1.5-hmod.upt \
    --runtime /private/artifacts/spotui-runtime.tar.xz \
    --auth-helper /private/output/spotui-auth-helper \
    --private-marker ACCOUNT_IDENTIFIER \
    --private-marker DEVICE_SERIAL \
    --output /private/output/spotui-0.1.0-beta.1-tester.tar.xz
```

The builder:

1. accepts only the exact tested firmware/runtime and published HiBy Mods v1.5 hashes;
2. requires the matched librespot 0.8.0 OAuth helper;
3. reconstructs and audits the firmware rootfs;
4. compares inherited build-path/driver findings with byte-identical files from
   the verified HiBy Mods base and verifies the upstream Shairport/WPA fingerprints;
5. permits only the known upstream Shairport PEM block;
6. extracts and hash-checks every runtime payload file;
7. scans unpacked and assembled files for personal/secret material;
8. adds SpotUI and HiBy Mods licenses, notices, privacy, and recovery guidance;
9. writes internal checksums and a source-commit record;
10. creates a deterministic XZ/CRC32 archive;
11. re-extracts, checksum-verifies, and privacy-scans the final result.

Generated bundle archives, helper binaries, `.upt` files, and runtime archives
must not be committed. The normal builder requires its release sources to be
committed and unchanged. `--allow-dirty-source` exists only for an unpublished
builder test and records that state inside the candidate.

## Public-release gate

Before uploading a candidate:

- verify its outer SHA-256 twice from independent copies;
- extract it into a new directory and run `sha256sum -c SHA256SUMS`;
- review every included text file;
- test the exact archive on the maintainer device;
- mark the GitHub release as a prerelease and provide one privacy-safe public
  feedback issue for voluntary tester results;
- preserve the upstream license/notice and clearly identify proprietary
  firmware boundaries;
- confirm recovery firmware for the exact model remains available;
- upload no credentials, cache, logs, WiFi data, private markers, or backups.

HiBy Mods states that its MIT license applies to project tooling, not the
proprietary firmware binaries. Public distribution of a further modified image
should retain that notice and be reviewed by the maintainer as a rights/risk
decision; this workflow is technical validation, not legal advice.
