# Privacy and credential boundary

This tester bundle is built to contain no maintainer or tester:

- Spotify username, password, access token, reusable credential, or cache;
- WiFi SSID, password, PSK, or device network configuration;
- ADB device serial;
- computer username or absolute home-directory path;
- private logs, database files, device snapshots, or backup files.

The release builder checks the assembled files and unpacked device payloads
for private markers, credential-shaped JSON, live OAuth URLs, access tokens,
WiFi assignments, private-key blocks, and sensitive filenames. It refuses an
unexpected match and does not print the matched value.

The inherited firmware includes upstream compiler source paths and Ingenic
driver symbol names. The gate accepts those generic findings only when the
containing file is byte-identical to the exact published HiBy Mods v1.5 base.
Explicit maintainer/tester markers are never accepted through that exception.

The unchanged musl runtime loader contains upstream CI runner source paths.
The gate accepts generic home-path findings from only that exact fingerprinted
loader file. It still scans the file for explicit private markers, credentials,
WiFi values, tokens, and private keys.

## Spotify authorization

`spotui-auth-helper` uses librespot 0.8.0 and Spotify's browser OAuth flow. The
Spotify client ID embedded by upstream librespot is a public application
identifier, not a password or client secret. This bundle contains no Spotify
client secret.

Authorization creates `credentials.json` in a mode-0700 temporary directory on
the tester's own computer. `onboard_spotify.py` validates it, stages it over
ADB, verifies its hash without displaying it, and activates it as mode 0600 in
`/usr/data/librespot-cache`. The temporary computer directory is then removed.
An existing device credential is retained as a private rollback copy.

Never upload `credentials.json`, `credentials.json.previous`,
`credentials.json.failed`, `librespot-cache`, device logs, or WiFi files.

## Upstream firmware exception

The exact verified HiBy Mods v1.5-derived firmware contains a static PEM block
inside its unchanged upstream `shairport` executable. The release gate permits
only that fingerprinted block and fails on any additional private-key block.
The `shairport` file, PEM block, and two generic WPA configuration files were
verified byte-for-byte against the untouched published HiBy Mods v1.5 image.
The WPA files contain no SSID or PSK assignment.

This inherited static protocol material is not generated from the maintainer's
or tester's device, account, network, or computer.
