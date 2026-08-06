#!/usr/bin/env python3
"""Create and atomically install a private librespot credential over ADB."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


DEVICE_CACHE_DIR = "/usr/data/librespot-cache"
DEVICE_CREDENTIALS = f"{DEVICE_CACHE_DIR}/credentials.json"
DEVICE_STAGED = f"{DEVICE_CREDENTIALS}.new"
DEVICE_PREVIOUS = f"{DEVICE_CREDENTIALS}.previous"
DEVICE_FAILED = f"{DEVICE_CREDENTIALS}.failed"
EXPECTED_AUTH_HELPER_PREFIX = "spotui-auth-helper 0.1.0-beta.2 (librespot 0.8.0)"
MAX_CREDENTIAL_BYTES = 128 * 1024


class OnboardingError(RuntimeError):
    """A safe, user-facing onboarding failure."""


def parse_arguments() -> argparse.Namespace:
    default_helper = Path(__file__).resolve().with_name("spotui-auth-helper")
    parser = argparse.ArgumentParser(
        description=(
            "Authorize Spotify on this computer and install only the resulting "
            "private librespot credential on a connected SpotUI device."
        )
    )
    parser.add_argument(
        "--auth-helper",
        type=Path,
        default=default_helper,
        help="path to the matched spotui-auth-helper binary",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        help="install an existing reusable credentials.json instead of running OAuth",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="restore the previous device credential without running OAuth",
    )
    parser.add_argument("--serial", help="ADB device serial when more than one is connected")
    parser.add_argument("--adb", default="adb", help="ADB executable (default: adb)")
    parser.add_argument(
        "--oauth-port",
        type=int,
        default=5588,
        help="localhost OAuth callback port (default: 5588)",
    )
    arguments = parser.parse_args()

    if arguments.rollback and arguments.credentials is not None:
        parser.error("--rollback and --credentials cannot be used together")
    if not 1 <= arguments.oauth_port <= 65535:
        parser.error("--oauth-port must be from 1 to 65535")

    return arguments


def run_command(
    command: list[str],
    *,
    capture: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if check and result.returncode != 0:
        detail = ""
        if capture and result.stderr:
            detail = f": {result.stderr.strip()}"
        raise OnboardingError(f"command failed ({command[0]}){detail}")
    return result


def resolve_adb(arguments: argparse.Namespace) -> list[str]:
    adb_path = shutil.which(arguments.adb)
    if adb_path is None:
        raise OnboardingError(f"ADB executable not found: {arguments.adb}")

    result = run_command([adb_path, "devices"])
    devices: list[tuple[str, str]] = []
    for line in result.stdout.splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 2:
            devices.append((fields[0], fields[1]))

    if arguments.serial:
        matching = [state for serial, state in devices if serial == arguments.serial]
        if not matching:
            raise OnboardingError(f"ADB device not found: {arguments.serial}")
        if matching[0] != "device":
            raise OnboardingError(
                f"ADB device {arguments.serial} is not ready ({matching[0]})"
            )
        return [adb_path, "-s", arguments.serial]

    ready = [serial for serial, state in devices if state == "device"]
    if len(ready) != 1:
        raise OnboardingError(
            f"expected exactly one ready ADB device, found {len(ready)}; use --serial"
        )
    return [adb_path, "-s", ready[0]]


def adb_shell(adb: list[str], command: str, *, check: bool = True) -> str:
    return run_command([*adb, "shell", command], check=check).stdout.strip()


def require_safe_device_state(adb: list[str]) -> None:
    runtime_state = adb_shell(
        adb,
        "test -f /usr/data/spotui_daemon && "
        "test -f /usr/data/start_spotui.sh && echo ready",
    )
    if runtime_state != "ready":
        raise OnboardingError("the connected device does not have the SpotUI runtime")

    active = adb_shell(
        adb,
        "ps | grep -E '[s]potui-ui-poc|[s]potui_daemon|[a]play|[s]tart_spotui' || true",
    )
    if active:
        raise OnboardingError(
            "SpotUI or its audio process is active; exit to the stock HiBy interface first"
        )


def validate_credentials(path: Path) -> None:
    try:
        metadata = path.stat()
    except OSError as error:
        raise OnboardingError(f"credential file is unavailable: {error}") from error
    if not path.is_file() or path.is_symlink():
        raise OnboardingError("credential path must be a regular file, not a symlink")
    if metadata.st_size <= 0 or metadata.st_size > MAX_CREDENTIAL_BYTES:
        raise OnboardingError("credential file has an unexpected size")
    if os.name == "posix" and metadata.st_mode & 0o077:
        raise OnboardingError("credential file must be private; set its mode to 0600")

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OnboardingError("credential file is not valid private librespot JSON") from error

    if not isinstance(value, dict):
        raise OnboardingError("credential file must contain one JSON object")
    username = value.get("username")
    auth_type = value.get("auth_type")
    auth_data = value.get("auth_data", value.get("encoded_auth_blob"))
    if not isinstance(username, str) or not username:
        raise OnboardingError("credential is not a reusable authenticated account cache")
    if not isinstance(auth_type, int) or not 0 <= auth_type <= 255:
        raise OnboardingError("credential has an invalid librespot authentication type")
    if not isinstance(auth_data, str):
        raise OnboardingError("credential is missing its encoded authentication data")
    try:
        decoded = base64.b64decode(auth_data, validate=True)
    except (ValueError, binascii.Error) as error:
        raise OnboardingError("credential authentication data is not valid base64") from error
    if not 16 <= len(decoded) <= 64 * 1024:
        raise OnboardingError("credential authentication data has an unexpected size")


def helper_version(helper: Path) -> None:
    if not helper.is_file() or not os.access(helper, os.X_OK):
        raise OnboardingError(f"matched auth helper is not executable: {helper}")
    result = run_command([str(helper), "--version"])
    if result.stdout.strip() != EXPECTED_AUTH_HELPER_PREFIX:
        raise OnboardingError(
            "auth helper version mismatch; use the helper bundled with this installer"
        )


def generate_credentials(helper: Path, oauth_port: int, output_dir: Path) -> Path:
    helper_version(helper)
    print("A browser will open for Spotify authorization.", flush=True)
    print("SpotUI never receives or requests your Spotify password.", flush=True)
    result = run_command(
        [
            str(helper),
            "--output-dir",
            str(output_dir),
            "--port",
            str(oauth_port),
        ],
        capture=False,
        check=False,
    )
    if result.returncode != 0:
        raise OnboardingError("Spotify authorization did not complete")
    credentials = output_dir / "credentials.json"
    validate_credentials(credentials)
    return credentials


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def device_sha256(adb: list[str], path: str) -> str:
    output = adb_shell(adb, f"sha256sum {path}")
    fields = output.split()
    if len(fields) < 2 or len(fields[0]) != 64:
        raise OnboardingError("could not verify the staged device credential")
    return fields[0]


def install_credentials(adb: list[str], credentials: Path) -> bool:
    validate_credentials(credentials)
    local_hash = file_sha256(credentials)

    adb_shell(
        adb,
        f"umask 077; mkdir -p {DEVICE_CACHE_DIR} && "
        f"chmod 700 {DEVICE_CACHE_DIR} && rm -f {DEVICE_STAGED}",
    )
    try:
        run_command([*adb, "push", str(credentials), DEVICE_STAGED])
        adb_shell(adb, f"chmod 600 {DEVICE_STAGED}")
        if device_sha256(adb, DEVICE_STAGED) != local_hash:
            raise OnboardingError("staged device credential hash mismatch")

        current_hash = adb_shell(
            adb,
            f"if test -f {DEVICE_CREDENTIALS}; then sha256sum {DEVICE_CREDENTIALS}; fi",
        ).split()
        if current_hash and current_hash[0] == local_hash:
            adb_shell(
                adb,
                f"chmod 600 {DEVICE_CREDENTIALS}; rm -f {DEVICE_STAGED}; sync",
            )
            return False

        activation = (
            "set -e; umask 077; "
            f"if test -f {DEVICE_CREDENTIALS}; then "
            f"cp {DEVICE_CREDENTIALS} {DEVICE_PREVIOUS}.new; "
            f"chmod 600 {DEVICE_PREVIOUS}.new; "
            f"mv {DEVICE_PREVIOUS}.new {DEVICE_PREVIOUS}; fi; "
            f"mv {DEVICE_STAGED} {DEVICE_CREDENTIALS}; "
            f"chmod 600 {DEVICE_CREDENTIALS}; chmod 700 {DEVICE_CACHE_DIR}; sync"
        )
        adb_shell(adb, activation)
        if device_sha256(adb, DEVICE_CREDENTIALS) != local_hash:
            raise OnboardingError("activated device credential hash mismatch")
        return True
    except Exception:
        adb_shell(adb, f"rm -f {DEVICE_STAGED}", check=False)
        raise


def rollback_credentials(adb: list[str]) -> None:
    command = (
        "set -e; umask 077; "
        f"test -f {DEVICE_PREVIOUS}; "
        f"cp {DEVICE_PREVIOUS} {DEVICE_STAGED}; chmod 600 {DEVICE_STAGED}; "
        f"if test -f {DEVICE_CREDENTIALS}; then "
        f"cp {DEVICE_CREDENTIALS} {DEVICE_FAILED}.new; "
        f"chmod 600 {DEVICE_FAILED}.new; "
        f"mv {DEVICE_FAILED}.new {DEVICE_FAILED}; fi; "
        f"mv {DEVICE_STAGED} {DEVICE_CREDENTIALS}; "
        f"chmod 600 {DEVICE_CREDENTIALS}; chmod 700 {DEVICE_CACHE_DIR}; sync"
    )
    result = run_command([*adb, "shell", command], check=False)
    if result.returncode != 0:
        raise OnboardingError("no previous device credential was available to restore")


def main() -> int:
    arguments = parse_arguments()
    try:
        adb = resolve_adb(arguments)
        require_safe_device_state(adb)

        if arguments.rollback:
            rollback_credentials(adb)
            print("Previous device credential restored.")
            print("Launch SpotUI and verify account access before removing any backup.")
            return 0

        if arguments.credentials is not None:
            changed = install_credentials(adb, arguments.credentials.resolve())
        else:
            with tempfile.TemporaryDirectory(prefix="spotui-auth-") as private_dir:
                output_dir = Path(private_dir)
                output_dir.chmod(0o700)
                credentials = generate_credentials(
                    arguments.auth_helper.resolve(),
                    arguments.oauth_port,
                    output_dir,
                )
                changed = install_credentials(adb, credentials)

        if changed:
            print("Credential onboarding complete; the previous device credential was preserved.")
        else:
            print("The device already had this credential; its permissions were secured.")
        print("Private temporary credentials have been removed from this computer.")
        print("Launch SpotUI and verify Liked Songs and playback.")
        return 0
    except OnboardingError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
