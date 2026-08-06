#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." >/dev/null 2>&1 && pwd)"
RELEASE_FILES="$SCRIPT_DIR/release"
PRIVACY_AUDITOR="$SCRIPT_DIR/audit_release_privacy.py"

VERSION="0.1.0-beta.2"
BUNDLE_NAME="spotui-${VERSION}-r3proii-hmod1.5-tester-linux-x86_64"
EXPECTED_FIRMWARE_SHA256="4821a75376ad9f624b3dbd6392ead76cff41fa3b1594e00e1261a4894eb51f6c"
EXPECTED_FIRMWARE_MD5="7860dde40285936473090aced1a1e9b7"
EXPECTED_RUNTIME_SHA256="2fd5c1fddb9d1f18ecef9569c0f1bd5abfa4f43c02554ebe5ed09da1d3802944"
EXPECTED_ROOTFS_SHA256="e34d001295ce57326c277e557a8724fb123d227503f70dcc3f542df54688e3b6"
EXPECTED_HMOD_BASE_SHA256="631af685977877f65288e371d49f3b2839681ee4ca4713234f498519e2ab33f2"
EXPECTED_RUNTIME_LOADER_SHA256="ad3247d5c5a22ee0076c28c5e80b841ea24c604687a855997b9eb8aa77db4d37"
EXPECTED_SHAIRPORT_SHA256="adbbdce5392b7fa9df356812447fe91b51f6837dc254be07ea5107c0364a9935"
EXPECTED_SHAIRPORT_PEM_SHA256="22ef66385dbfcba1e2e768f62d6a2f0d6a73fd0b26efcff1454e6db026af98a1"
EXPECTED_WPA_SHA256="3dfb3034b3da28b307616686749f685ad041a9e12ffab89e0d03712e2a35e790"
EXPECTED_WPA_DBUS_SHA256="e5a24b54f6db045b68c72b5e555a62db388207b68f0b7137add0117af9f56841"
ARCHIVE_TIME="2026-07-27 00:00:00 UTC"

FIRMWARE=""
HMOD_BASE=""
RUNTIME=""
AUTH_HELPER=""
OUTPUT=""
ALLOW_DIRTY=0
PRIVATE_MARKERS=()

usage() {
    cat <<EOF
Usage:
  $(basename "$0") \\
    --firmware PATH_TO_TESTED_UPT \\
    --hmod-base PATH_TO_ORIGINAL_HMOD_V1_5_UPT \\
    --runtime PATH_TO_TESTED_RUNTIME_TAR_XZ \\
    --auth-helper PATH_TO_PRIVACY_REMAPPED_HELPER \\
    --output PATH_TO_NEW_BUNDLE_TAR_XZ \\
    [--private-marker PRIVATE_VALUE]...

The builder accepts only the exact device-tested firmware/runtime pair. Each
private marker is checked without being copied into the bundle or its reports.
Use --allow-dirty-source only for an unpublished builder test.
EOF
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

hash_file() {
    sha256sum "$1" | awk '{print $1}'
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --firmware)
            [ "$#" -ge 2 ] || fail "--firmware requires a path"
            FIRMWARE="$2"
            shift 2
            ;;
        --hmod-base)
            [ "$#" -ge 2 ] || fail "--hmod-base requires a path"
            HMOD_BASE="$2"
            shift 2
            ;;
        --runtime)
            [ "$#" -ge 2 ] || fail "--runtime requires a path"
            RUNTIME="$2"
            shift 2
            ;;
        --auth-helper)
            [ "$#" -ge 2 ] || fail "--auth-helper requires a path"
            AUTH_HELPER="$2"
            shift 2
            ;;
        --output)
            [ "$#" -ge 2 ] || fail "--output requires a path"
            OUTPUT="$2"
            shift 2
            ;;
        --private-marker)
            [ "$#" -ge 2 ] || fail "--private-marker requires a value"
            [ -n "$2" ] || fail "--private-marker cannot be empty"
            PRIVATE_MARKERS+=("$2")
            shift 2
            ;;
        --allow-dirty-source)
            ALLOW_DIRTY=1
            shift
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

[ -n "$FIRMWARE" ] || fail "--firmware is required"
[ -n "$HMOD_BASE" ] || fail "--hmod-base is required"
[ -n "$RUNTIME" ] || fail "--runtime is required"
[ -n "$AUTH_HELPER" ] || fail "--auth-helper is required"
[ -n "$OUTPUT" ] || fail "--output is required"

for input in "$FIRMWARE" "$HMOD_BASE" "$RUNTIME" "$AUTH_HELPER"; do
    [ -f "$input" ] || fail "input file not found: $input"
done
[ ! -e "$OUTPUT" ] || fail "output already exists: $OUTPUT"
[ -d "$(dirname "$OUTPUT")" ] || fail "output directory does not exist"

for command_name in \
    7z awk cat file find git grep install md5sum mkdir python3 rg sha256sum \
    sort strings tar unsquashfs wc xargs xz
do
    command -v "$command_name" >/dev/null 2>&1 ||
        fail "missing required command: $command_name"
done

REQUIRED_SOURCES=(
    "$PRIVACY_AUDITOR"
    "$SCRIPT_DIR/onboard_spotify.py"
    "$RELEASE_FILES/README.md"
    "$RELEASE_FILES/PRIVACY.md"
    "$RELEASE_FILES/HIBY-MODS-LICENSE.txt"
    "$RELEASE_FILES/HIBY-MODS-NOTICE.md"
    "$REPO_ROOT/LICENSE"
    "$REPO_ROOT/DISCLAIMER.md"
    "$REPO_ROOT/SECURITY.md"
    "$REPO_ROOT/THIRD_PARTY.md"
    "$REPO_ROOT/docs/credential-onboarding.md"
    "$REPO_ROOT/docs/recovery.md"
    "$REPO_ROOT/docs/tester-installer.md"
)
for source_file in "${REQUIRED_SOURCES[@]}"; do
    [ -f "$source_file" ] || fail "required release source missing: $source_file"
done

if [ "$ALLOW_DIRTY" -eq 0 ]; then
    for source_file in "${REQUIRED_SOURCES[@]}" "$0"; do
        relative_source="${source_file#"$REPO_ROOT/"}"
        git -C "$REPO_ROOT" ls-files --error-unmatch "$relative_source" >/dev/null 2>&1 ||
            fail "release source is not committed: $relative_source"
    done
    git -C "$REPO_ROOT" diff --quiet -- "${REQUIRED_SOURCES[@]}" "$0" ||
        fail "release sources have unstaged changes"
    git -C "$REPO_ROOT" diff --cached --quiet -- "${REQUIRED_SOURCES[@]}" "$0" ||
        fail "release sources have staged uncommitted changes"
fi

[ "$(hash_file "$FIRMWARE")" = "$EXPECTED_FIRMWARE_SHA256" ] ||
    fail "firmware is not the exact device-tested image"
[ "$(hash_file "$HMOD_BASE")" = "$EXPECTED_HMOD_BASE_SHA256" ] ||
    fail "HiBy Mods base is not the exact published v1.5 image"
[ "$(md5sum "$FIRMWARE" | awk '{print $1}')" = "$EXPECTED_FIRMWARE_MD5" ] ||
    fail "firmware MD5 mismatch"
[ "$(hash_file "$RUNTIME")" = "$EXPECTED_RUNTIME_SHA256" ] ||
    fail "runtime archive is not the exact device-tested payload"
[ "$("$AUTH_HELPER" --version)" = "spotui-auth-helper 0.1.0-beta.2 (librespot 0.8.0)" ] ||
    fail "auth helper version mismatch"
file -L "$AUTH_HELPER" | grep -q "ELF 64-bit LSB pie executable, x86-64" ||
    fail "auth helper is not the expected x86-64 Linux executable"

WORK="$(mktemp -d /tmp/spotui-tester-bundle.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

AUDIT_MARKERS=(
    --private-marker "$REPO_ROOT"
    --private-marker "$(dirname "$REPO_ROOT")"
)
for marker in "${PRIVATE_MARKERS[@]}"; do
    AUDIT_MARKERS+=(--private-marker "$marker")
done

echo "[1/7] Auditing the privacy-remapped host helper"
python3 "$PRIVACY_AUDITOR" \
    --root "$AUTH_HELPER" \
    "${AUDIT_MARKERS[@]}"

echo "[2/7] Verifying and auditing the tested firmware"
mkdir -p "$WORK/hmod-base-upt"
7z x "$HMOD_BASE" "-o$WORK/hmod-base-upt" -y >/dev/null
cat "$WORK"/hmod-base-upt/ota_v0/rootfs.squashfs.* > "$WORK/hmod-base-rootfs.squashfs"
unsquashfs -f -d "$WORK/hmod-base-rootfs" "$WORK/hmod-base-rootfs.squashfs" >/dev/null

mkdir -p "$WORK/firmware-upt"
7z x "$FIRMWARE" "-o$WORK/firmware-upt" -y >/dev/null
cat "$WORK"/firmware-upt/ota_v0/rootfs.squashfs.* > "$WORK/rootfs.squashfs"
[ "$(hash_file "$WORK/rootfs.squashfs")" = "$EXPECTED_ROOTFS_SHA256" ] ||
    fail "packaged firmware rootfs mismatch"
unsquashfs -f -d "$WORK/rootfs" "$WORK/rootfs.squashfs" >/dev/null

[ "$(hash_file "$WORK/rootfs/usr/bin/shairport")" = "$EXPECTED_SHAIRPORT_SHA256" ] ||
    fail "upstream Shairport binary changed unexpectedly"
[ "$(hash_file "$WORK/rootfs/etc/wpa_supplicant.conf")" = "$EXPECTED_WPA_SHA256" ] ||
    fail "upstream WPA configuration changed unexpectedly"
[ "$(hash_file "$WORK/rootfs/etc/dbus-1/system.d/wpa_supplicant.conf")" = "$EXPECTED_WPA_DBUS_SHA256" ] ||
    fail "upstream WPA D-Bus policy changed unexpectedly"

python3 "$PRIVACY_AUDITOR" \
    --root "$WORK/rootfs" \
    --allow-symlinks \
    --allow-private-key-sha256 "$EXPECTED_SHAIRPORT_PEM_SHA256" \
    --allow-sensitive-path etc/wpa_supplicant.conf \
    --allow-sensitive-path etc/dbus-1/system.d/wpa_supplicant.conf \
    --allow-identical-baseline-root "$WORK/hmod-base-rootfs" \
    "${AUDIT_MARKERS[@]}"

echo "[3/7] Verifying and auditing the tested runtime"
xz -t "$RUNTIME"
mkdir -p "$WORK/runtime"
xz -dc "$RUNTIME" | tar -xf - -C "$WORK/runtime"
(
    cd "$WORK/runtime"
    sha256sum -c SHA256SUMS >/dev/null
)
RUNTIME_FILE_COUNT="$(find "$WORK/runtime" -maxdepth 1 -type f | wc -l)"
[ "$RUNTIME_FILE_COUNT" -eq 8 ] || fail "runtime archive contains unexpected files"
python3 "$PRIVACY_AUDITOR" \
    --root "$WORK/runtime" \
    --allow-generic-file-sha256 "$EXPECTED_RUNTIME_LOADER_SHA256" \
    "${AUDIT_MARKERS[@]}"

echo "[4/7] Assembling the tester directory"
BUNDLE_PARENT="$WORK/bundle"
BUNDLE_ROOT="$BUNDLE_PARENT/$BUNDLE_NAME"
mkdir -p "$BUNDLE_ROOT/docs"

install -m 0644 "$FIRMWARE" "$BUNDLE_ROOT/r3proii.upt"
install -m 0644 "$RUNTIME" "$BUNDLE_ROOT/spotui-runtime.tar.xz"
install -m 0755 "$AUTH_HELPER" "$BUNDLE_ROOT/spotui-auth-helper"
install -m 0755 "$SCRIPT_DIR/onboard_spotify.py" "$BUNDLE_ROOT/onboard_spotify.py"
install -m 0644 "$RELEASE_FILES/README.md" "$BUNDLE_ROOT/README.md"
install -m 0644 "$RELEASE_FILES/PRIVACY.md" "$BUNDLE_ROOT/PRIVACY.md"
install -m 0644 "$RELEASE_FILES/HIBY-MODS-LICENSE.txt" "$BUNDLE_ROOT/HIBY-MODS-LICENSE.txt"
install -m 0644 "$RELEASE_FILES/HIBY-MODS-NOTICE.md" "$BUNDLE_ROOT/HIBY-MODS-NOTICE.md"
install -m 0644 "$REPO_ROOT/LICENSE" "$BUNDLE_ROOT/SPOTUI-LICENSE.txt"
install -m 0644 "$REPO_ROOT/DISCLAIMER.md" "$BUNDLE_ROOT/DISCLAIMER.md"
install -m 0644 "$REPO_ROOT/SECURITY.md" "$BUNDLE_ROOT/SECURITY.md"
install -m 0644 "$REPO_ROOT/THIRD_PARTY.md" "$BUNDLE_ROOT/THIRD_PARTY.md"
install -m 0644 "$REPO_ROOT/docs/credential-onboarding.md" "$BUNDLE_ROOT/docs/credential-onboarding.md"
install -m 0644 "$REPO_ROOT/docs/recovery.md" "$BUNDLE_ROOT/docs/recovery.md"
install -m 0644 "$REPO_ROOT/docs/tester-installer.md" "$BUNDLE_ROOT/docs/tester-installer.md"

SOURCE_COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD)"
SOURCE_STATE="committed"
[ "$ALLOW_DIRTY" -eq 0 ] || SOURCE_STATE="unpublished-development-test"
{
    echo "SpotUI version: $VERSION"
    echo "SpotUI source commit: $SOURCE_COMMIT"
    echo "Source state: $SOURCE_STATE"
    echo "Target device: HiBy R3 Pro II"
    echo "Firmware base: HiBy Mods v1.5"
    echo "HiBy Mods v1.5 SHA-256: $EXPECTED_HMOD_BASE_SHA256"
    echo "SpotUI firmware SHA-256: $EXPECTED_FIRMWARE_SHA256"
    echo "SpotUI runtime SHA-256: $EXPECTED_RUNTIME_SHA256"
    echo "Host helper SHA-256: $(hash_file "$AUTH_HELPER")"
} > "$BUNDLE_ROOT/BUILD-INFO.txt"

(
    cd "$BUNDLE_ROOT"
    find . -type f ! -name SHA256SUMS -print0 |
        sort -z |
        xargs -0 sha256sum > SHA256SUMS
)

echo "[5/7] Auditing the complete assembled bundle"
if find "$BUNDLE_ROOT" -type l | rg -q .; then
    fail "assembled bundle contains a symbolic link"
fi
python3 "$PRIVACY_AUDITOR" \
    --root "$BUNDLE_ROOT" \
    --skip-path r3proii.upt \
    --skip-path spotui-runtime.tar.xz \
    "${AUDIT_MARKERS[@]}"

echo "[6/7] Creating the deterministic release archive"
mkdir -p "$WORK/output"
TEMP_OUTPUT="$WORK/output/$(basename "$OUTPUT")"
tar \
    --sort=name \
    --mtime="$ARCHIVE_TIME" \
    --owner=0 \
    --group=0 \
    --numeric-owner \
    -C "$BUNDLE_PARENT" \
    -cf - \
    "$BUNDLE_NAME" |
    xz -4e -T1 --check=crc32 > "$TEMP_OUTPUT"
xz -t "$TEMP_OUTPUT"

echo "[7/7] Re-extracting and verifying the final archive"
mkdir -p "$WORK/verify"
xz -dc "$TEMP_OUTPUT" | tar -xf - -C "$WORK/verify"
(
    cd "$WORK/verify/$BUNDLE_NAME"
    sha256sum -c SHA256SUMS >/dev/null
)
python3 "$PRIVACY_AUDITOR" \
    --root "$WORK/verify/$BUNDLE_NAME" \
    --skip-path r3proii.upt \
    --skip-path spotui-runtime.tar.xz \
    "${AUDIT_MARKERS[@]}"

install -m 0644 "$TEMP_OUTPUT" "$OUTPUT"

echo "Verified local tester bundle complete"
echo "Output: $OUTPUT"
echo "SHA-256: $(hash_file "$OUTPUT")"
echo "No file was uploaded or pushed."
