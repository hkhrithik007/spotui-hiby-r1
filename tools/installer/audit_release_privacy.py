#!/usr/bin/env python3
"""Fail closed when a release tree contains personal or secret material."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys


PRIVATE_KEY_PATTERN = re.compile(
    rb"-----BEGIN ([A-Z0-9]+ )*PRIVATE KEY-----\r?\n"
    rb"[A-Za-z0-9+/=\r\n]{64,}"
    rb"-----END ([A-Z0-9]+ )*PRIVATE KEY-----"
)
GENERIC_PATTERNS = (
    ("absolute-home-path", re.compile(rb"/(home|Users)/[A-Za-z0-9._-]+/")),
    ("windows-user-path", re.compile(rb"[A-Za-z]:\\Users\\[A-Za-z0-9._-]+\\")),
    ("ingenic-device-serial", re.compile(rb"ingenic_[A-Za-z0-9_-]+", re.IGNORECASE)),
    ("aws-access-key", re.compile(rb"AKIA[0-9A-Z]{16}")),
    ("github-token", re.compile(rb"gh[pousr]_[A-Za-z0-9_]{30,}")),
    (
        "credential-auth-data",
        re.compile(rb'"(auth_data|encoded_auth_blob)"\s*:\s*"[A-Za-z0-9+/=]{16,}"'),
    ),
    (
        "oauth-token-json",
        re.compile(rb'"(access_token|refresh_token)"\s*:\s*"[^"\r\n]{16,}"'),
    ),
    (
        "live-oauth-url",
        re.compile(rb"accounts\.spotify\.com/authorize\?[^\s\x00]*state="),
    ),
    (
        "wifi-network-value",
        re.compile(
            rb"(?mi)^[ \t]*(ssid|psk)[ \t]*=[ \t]*"
            rb'(?:"[^"\r\n]+"|[^\s#][^\r\n]*)'
        ),
    ),
)
SENSITIVE_NAMES = {
    "credentials.json",
    "wpa_supplicant.conf",
}
SENSITIVE_SUFFIXES = {
    ".key",
    ".p12",
    ".pfx",
    ".token",
}
BASELINE_ALLOWED_CATEGORIES = {
    "absolute-home-path",
    "windows-user-path",
    "ingenic-device-serial",
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan one file or directory without printing matched secret values."
    )
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--private-marker", action="append", default=[])
    parser.add_argument("--allow-private-key-sha256", action="append", default=[])
    parser.add_argument("--allow-generic-file-sha256", action="append", default=[])
    parser.add_argument("--allow-sensitive-path", action="append", default=[])
    parser.add_argument("--allow-identical-baseline-root", type=Path)
    parser.add_argument("--skip-path", action="append", default=[])
    parser.add_argument("--allow-symlinks", action="store_true")
    return parser.parse_args()


def iter_paths(root: Path) -> list[tuple[Path, Path]]:
    if root.is_file():
        return [(root, Path(root.name))]
    if not root.is_dir():
        raise ValueError("audit root is not a regular file or directory")
    return [(path, path.relative_to(root)) for path in sorted(root.rglob("*"))]


def main() -> int:
    arguments = parse_arguments()
    root = arguments.root.resolve()
    allowed_key_hashes = {value.lower() for value in arguments.allow_private_key_sha256}
    allowed_generic_hashes = {
        value.lower() for value in arguments.allow_generic_file_sha256
    }
    allowed_sensitive_paths = {
        Path(value).as_posix().lstrip("./") for value in arguments.allow_sensitive_path
    }
    skipped_paths = {Path(value).as_posix().lstrip("./") for value in arguments.skip_path}
    skipped_path_counts = {value: 0 for value in skipped_paths}
    baseline_root = (
        arguments.allow_identical_baseline_root.resolve()
        if arguments.allow_identical_baseline_root
        else None
    )
    if baseline_root is not None and not baseline_root.is_dir():
        print("privacy audit error: baseline root is not a directory", file=sys.stderr)
        return 2
    private_markers = [
        value.encode("utf-8").lower() for value in arguments.private_marker if value
    ]
    findings: list[tuple[str, str]] = []
    allowed_key_counts = {value: 0 for value in allowed_key_hashes}
    allowed_generic_files_seen: set[str] = set()
    scanned_files = 0

    try:
        paths = iter_paths(root)
    except (OSError, ValueError) as error:
        print(f"privacy audit error: {error}", file=sys.stderr)
        return 2

    for path, relative in paths:
        relative_text = relative.as_posix().lstrip("./")
        if relative_text in skipped_paths:
            if not path.is_file():
                findings.append((relative_text, "skip-path-is-not-a-regular-file"))
            skipped_path_counts[relative_text] += 1
            continue
        if path.is_symlink():
            if not arguments.allow_symlinks:
                findings.append((relative_text, "symbolic-link"))
            continue
        if not path.is_file():
            continue

        scanned_files += 1
        lower_relative = relative_text.lower().encode("utf-8")
        for index, marker in enumerate(private_markers, start=1):
            if marker in lower_relative:
                findings.append((relative_text, f"private-marker-{index}-in-path"))

        lower_name = path.name.lower()
        sensitive = (
            lower_name in SENSITIVE_NAMES
            or path.suffix.lower() in SENSITIVE_SUFFIXES
            or "librespot-cache" in {part.lower() for part in relative.parts}
        )
        if sensitive and relative_text not in allowed_sensitive_paths:
            findings.append((relative_text, "sensitive-filename"))

        try:
            data = path.read_bytes()
        except OSError:
            findings.append((relative_text, "unreadable-file"))
            continue
        lower_data = data.lower()

        for index, marker in enumerate(private_markers, start=1):
            if marker in lower_data:
                findings.append((relative_text, f"private-marker-{index}-in-content"))

        for category, pattern in GENERIC_PATTERNS:
            if pattern.search(data):
                digest = hashlib.sha256(data).hexdigest()
                if digest in allowed_generic_hashes and category in BASELINE_ALLOWED_CATEGORIES:
                    allowed_generic_files_seen.add(digest)
                    continue
                if baseline_root is not None and category in BASELINE_ALLOWED_CATEGORIES:
                    baseline_path = baseline_root / relative
                    try:
                        baseline_data = baseline_path.read_bytes()
                    except OSError:
                        baseline_data = b""
                    if baseline_data == data and pattern.search(baseline_data):
                        continue
                findings.append((relative_text, category))

        for match in PRIVATE_KEY_PATTERN.finditer(data):
            digest = hashlib.sha256(match.group(0)).hexdigest()
            if digest in allowed_key_hashes:
                allowed_key_counts[digest] += 1
            else:
                findings.append((relative_text, "embedded-private-key"))

    for digest, count in allowed_key_counts.items():
        if count == 0:
            findings.append((".", "required-known-private-key-exception-not-found"))
    for digest in allowed_generic_hashes:
        if digest not in allowed_generic_files_seen:
            findings.append((".", "required-known-generic-file-exception-not-found"))
    for relative_text, count in skipped_path_counts.items():
        if count == 0:
            findings.append((relative_text, "requested-skip-path-not-found"))

    if findings:
        print("PRIVACY AUDIT FAILED", file=sys.stderr)
        for relative_text, category in findings[:50]:
            print(f"  {relative_text}: {category}", file=sys.stderr)
        if len(findings) > 50:
            print(f"  ... {len(findings) - 50} additional findings", file=sys.stderr)
        return 1

    allowed_count = sum(allowed_key_counts.values())
    print(
        f"Privacy audit passed: {scanned_files} files, "
        f"{allowed_count} fingerprinted private-key exception(s), "
        f"{len(allowed_generic_files_seen)} fingerprinted generic-file exception(s), "
        f"{sum(skipped_path_counts.values())} separately audited archive(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
