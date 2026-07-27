#!/usr/bin/env python3
"""Apply the reviewed SpotUI launcher integration to an HMOD v1.5 rootfs."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


HMOD_V15_PLAYER_SHA256 = (
    "b4ca19e33dc79c250115f37b23c445c4eb7f42adf1a2198e26109ef2b79dcb09"
)
SPOTUI_PLAYER_SHA256 = (
    "e0cfb5455eb121c04392373c2315956a3ce45a6fcfb61b52ad5e0e1c7640000b"
)
HMOD_V15_PLAYER_SH_SHA256 = (
    "1ed03a80239032c6d363e8bdc9b6485dacac086e2bfe61403866a7c40fd25857"
)
SPOTUI_PLAYER_SH_SHA256 = (
    "8cb194b4890fcfafef941e4019c53cc823cd4e8d94e4ece75077c3a861e220d5"
)
BACKUP_PLAYER_SHA256 = (
    "4df2dcd0b23c233da37a25853b8a1843dc93a218ff9ec251abd88466443a664d"
)

# These four replacements are the complete 69-byte SpotUI delta from the
# published HMOD v1.5 player. Whole instruction/string regions are checked so
# that the patch cannot be applied to a merely similar proprietary binary.
PLAYER_PATCHES = (
    (
        1_391_968,
        bytes.fromhex(
            "c8 ff bd 27 2c 00 b0 af 34 00 bf af 30 00 b1 af "
            "50 00 b1 8c 01 00 10 24 00 41 1d 0c 28 00 24 8e "
            "06 00 40 14 34 00 bf 8f"
        ),
        bytes.fromhex(
            "e8 ff bd 27 14 00 bf af 94 00 04 3c 04 23 84 24 "
            "24 9c 23 0c 00 00 00 00 14 00 bf 8f 00 00 02 24 "
            "08 00 e0 03 18 00 bd 27"
        ),
    ),
    (
        1_485_632,
        bytes.fromhex("d0 fe bd 27 2c 01 bf af"),
        bytes.fromhex("58 4f 15 08 00 00 00 00"),
    ),
    (
        5_448_452,
        bytes(28),
        b"sh /usr/data/start_spotui.sh",
    ),
    (
        5_454_516,
        bytes.fromhex("20 b0 56"),
        bytes.fromhex("60 3d 55"),
    ),
)

PLAYER_SH_OLD = b"/usr/bin/hiby_player\nsleep 1\nreboot"
PLAYER_SH_NEW = b"""/usr/bin/hiby_player
sleep 1
# SpotUI GUI-launch guard:
# If Qobuz was repurposed to start SpotUI, hiby_player may exit intentionally.
# Do not reboot while the SpotUI launcher/UI/daemon is alive.
if ps | grep -q "[s]tart_spotui"; then
    exit 0
fi
if ps | grep -q "[s]potui-ui-poc"; then
    exit 0
fi
if ps | grep -q "[s]potui_daemon"; then
    exit 0
fi

reboot
"""

LABEL_HASHES = {
    "english": (
        "4b823faef431df28f4a9b792b4d13a648827696d0662dc67df7783e46e283d2a",
        "393ca4e890e51af95544602b9726f68b232ca055b8f97cd530dfbfd196d82263",
    ),
    "french": (
        "392909df5611a70d0b682729884dfa4bb5a42e28f7b7c80f7c164474276cfcde",
        "7092383e54d13fe9092736b4af1dbceb8c4112e0fb019a40f7914b08ded5ecde",
    ),
    "german": (
        "49b3cf088242bb4cd7e6ae6883afae862e531a5694846ca6dfcd8bb0d58a47f0",
        "de0f6ce1e4086cadf566b0917605c400a853fabae9c4d33436ccb2b6a8fae4ca",
    ),
    "italy": (
        "3fa0272764aa6ed7eb2a2b51d977a6934379c7a661addc0e9407c6abaac5922c",
        "8f0968e2d90c097af7ec2bc944b54eac202c3b2243e49942e4010c2ddcaeffd3",
    ),
    "japanese": (
        "77113fab4396b2c40d6e2e25f51cf30ab3453c93ed4ac059bcfcaa4c733f707b",
        "bff3f3b66098b2450d9dcefdec477eb94fd7605730ae32a15c143d23d2f68c7f",
    ),
    "korean": (
        "91438dc7fba323e767a64b561d2580dbfe567680760eb6bca81f9b20d135884f",
        "06a8cc84351055ed3d309b5b932a3efadc19e6b4fb36b90bd29bcc363990b5df",
    ),
    "poland": (
        "e792e47601b6ab8a987ccf10f37936d1f22dd08802661e9bffdec528ef49cd5c",
        "28cf2c15dcd9dd95313e6df77f5651bb05fce72ca51827bf6c3f15bb42725276",
    ),
    "russian": (
        "f73b81c47299c160966b302145e28175c72bc6b65da6000baac00f7b089bf14b",
        "23254f37bc9a13a19cd07d63ef42ba2e2218868a3a27de78be97f3b85b64378b",
    ),
    "simplified_chinese": (
        "b84711c2598a6184036558161b8278c2322e0b12e4b417ddd52768c31cdb2b1f",
        "a0cb25f256250497a2111befa169318a8d4e0c021ba1c0a929f26afb7908a2cc",
    ),
    "spain": (
        "5722c47a2ea6f63e5566c7e60710339c7955056b31f1a26ae942fc18a277aa90",
        "255560f3f56a0768da7f9dc646a6fa70e9a29dee24a3b20563e3b47bd68e2539",
    ),
    "thai": (
        "4228d4f504418dca63fb94340698ce8ced725ce9cb4b36a8c0bca668f316bb09",
        "a59f445f4f0ffc458e0b772c4494f62e03a7796fef80f750eca8ab15b6273d81",
    ),
    "traditional_chinese": (
        "dc77859acfabe1b323f4e30dbaaa23e16f24b04e22875d43940b7f10e2951320",
        "d0db04412e2c19bc1c3f821d8d93ffff6f8c3750ef98dfdcd6d11bfe14f45fb9",
    ),
    "ukrainian": (
        "b2bcf07b6fd8044447da40e3626578a2a4bd610d6651579709fa8003b532eef1",
        "43d06f27e6ee517e00e6754db3d06b2b8f2d1a37175313df28bb109284470d23",
    ),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_hash(path: Path, data: bytes, expected: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise RuntimeError(f"{path}: SHA-256 mismatch: {actual}")


def patch_player(root: Path) -> None:
    path = root / "usr/bin/hiby_player"
    data = bytearray(path.read_bytes())
    require_hash(path, data, HMOD_V15_PLAYER_SHA256)

    for offset, old, new in PLAYER_PATCHES:
        if len(old) != len(new):
            raise RuntimeError(f"internal patch length mismatch at {offset}")
        if data[offset : offset + len(old)] != old:
            raise RuntimeError(f"{path}: unexpected bytes at offset {offset}")
        data[offset : offset + len(old)] = new

    require_hash(path, data, SPOTUI_PLAYER_SHA256)
    path.write_bytes(data)


def patch_player_shell(root: Path) -> None:
    path = root / "usr/bin/hiby_player.sh"
    data = path.read_bytes()
    require_hash(path, data, HMOD_V15_PLAYER_SH_SHA256)
    if data.count(PLAYER_SH_OLD) != 1:
        raise RuntimeError(f"{path}: expected launcher/reboot block not found once")
    patched = data.replace(PLAYER_SH_OLD, PLAYER_SH_NEW)
    require_hash(path, patched, SPOTUI_PLAYER_SH_SHA256)
    path.write_bytes(patched)


def verify_backup_player(root: Path) -> None:
    path = root / "usr/bin/hiby_player.bak"
    require_hash(path, path.read_bytes(), BACKUP_PLAYER_SHA256)


def patch_labels(root: Path) -> None:
    old = "<qobuz>Qobuz</qobuz>".encode("utf-16le")
    new = "<qobuz>SpotUI</qobuz>".encode("utf-16le")

    for language, (input_hash, output_hash) in LABEL_HASHES.items():
        path = root / f"usr/resource/str/{language}/tidal.ini"
        data = path.read_bytes()
        require_hash(path, data, input_hash)
        if data.count(old) != 1:
            raise RuntimeError(f"{path}: expected Qobuz label not found once")
        patched = data.replace(old, new)
        require_hash(path, patched, output_hash)
        path.write_bytes(patched)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} ROOTFS", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: rootfs directory not found: {root}", file=sys.stderr)
        return 1

    try:
        patch_player(root)
        patch_player_shell(root)
        verify_backup_player(root)
        patch_labels(root)
    except (OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print("Verified HMOD v1.5 SpotUI launcher patch complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
