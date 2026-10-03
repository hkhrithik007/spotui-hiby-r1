#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." >/dev/null 2>&1 && pwd)"
MANIFEST="$SCRIPT_DIR/Cargo.toml"
PRIVACY_AUDITOR="$REPO_ROOT/tools/installer/audit_release_privacy.py"
OUTPUT=""

usage() {
    cat <<EOF
Usage: $(basename "$0") --output PATH

Builds the locked x86-64 Linux SpotUI OAuth helper with local filesystem paths
remapped, verifies it, and writes it to a new output path.
EOF
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --output)
            [ "$#" -ge 2 ] || fail "--output requires a path"
            OUTPUT="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            fail "unknown argument: $1"
            ;;
    esac
done

[ -n "$OUTPUT" ] || fail "--output is required"
[ ! -e "$OUTPUT" ] || fail "output already exists: $OUTPUT"
[ -d "$(dirname "$OUTPUT")" ] || fail "output directory does not exist"
[ -f "$PRIVACY_AUDITOR" ] || fail "privacy auditor is missing"

for command_name in cargo file grep install python3 rg sha256sum strings; do
    command -v "$command_name" >/dev/null 2>&1 ||
        fail "missing required command: $command_name"
done

BUILD_ROOT="$(mktemp -d /tmp/spotui-auth-release.XXXXXX)"
trap 'rm -rf "$BUILD_ROOT"' EXIT

BUILD_HOME="$(dirname "$REPO_ROOT")"
RUSTFLAGS_VALUE="--remap-path-prefix=/home=/build/source --remap-path-prefix=$BUILD_ROOT=/build/target"

echo "Building privacy-remapped SpotUI OAuth helper"
env \
    CARGO_INCREMENTAL=0 \
    CARGO_TARGET_DIR="$BUILD_ROOT/target" \
    SOURCE_DATE_EPOCH=1768509938 \
    RUSTFLAGS="$RUSTFLAGS_VALUE" \
    cargo build \
        --release \
        --locked \
        --manifest-path "$MANIFEST"

BINARY="$BUILD_ROOT/target/release/spotui-auth-helper"
[ -f "$BINARY" ] || fail "Cargo did not create the expected helper binary"

[ "$("$BINARY" --version)" = "spotui-auth-helper 0.1.0-beta.2 (librespot 0.8.0)" ] ||
    fail "helper version mismatch"
file -L "$BINARY" | grep -q "ELF 64-bit LSB pie executable, x86-64" ||
    fail "helper is not the expected x86-64 Linux executable"

if strings -a "$BINARY" | rg -F -q "$BUILD_HOME"; then
    fail "helper still contains the local build-home path"
fi
if strings -a "$BINARY" | rg -F -q "$REPO_ROOT"; then
    fail "helper still contains the local repository path"
fi

python3 "$PRIVACY_AUDITOR" \
    --root "$BINARY" \
    --private-marker "$BUILD_HOME" \
    --private-marker "$REPO_ROOT"

install -m 0755 "$BINARY" "$OUTPUT"

echo "Verified helper: $OUTPUT"
file -L "$OUTPUT"
sha256sum "$OUTPUT"
