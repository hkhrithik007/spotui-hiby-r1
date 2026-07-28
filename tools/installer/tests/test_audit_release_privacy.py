from __future__ import annotations

from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import unittest


AUDITOR = Path(__file__).resolve().parents[1] / "audit_release_privacy.py"


class PrivacyAuditTests(unittest.TestCase):
    def run_audit(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AUDITOR), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_accepts_generic_finding_only_from_identical_baseline_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            baseline = root / "baseline"
            candidate.mkdir()
            baseline.mkdir()
            content = b"compiled from /home/upstream/project/source.c"
            (candidate / "binary").write_bytes(content)
            (baseline / "binary").write_bytes(content)

            result = self.run_audit(
                "--root",
                str(candidate),
                "--allow-identical-baseline-root",
                str(baseline),
            )

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_generic_finding_when_baseline_file_differs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            baseline = root / "baseline"
            candidate.mkdir()
            baseline.mkdir()
            (candidate / "binary").write_bytes(b"/home/local/project")
            (baseline / "binary").write_bytes(b"/home/upstream/project")

            result = self.run_audit(
                "--root",
                str(candidate),
                "--allow-identical-baseline-root",
                str(baseline),
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("absolute-home-path", result.stderr)

    def test_accepts_generic_finding_only_for_exact_file_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            content = b"compiled by /home/runner/toolchain"
            (root / "loader").write_bytes(content)
            digest = hashlib.sha256(content).hexdigest()

            result = self.run_audit(
                "--root",
                str(root),
                "--allow-generic-file-sha256",
                digest,
            )

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_missing_generic_file_hash_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_audit(
                "--root",
                temporary,
                "--allow-generic-file-sha256",
                "0" * 64,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("required-known-generic-file-exception-not-found", result.stderr)

    def test_never_baseline_allows_explicit_private_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            baseline = root / "baseline"
            candidate.mkdir()
            baseline.mkdir()
            content = b"account-private-marker"
            (candidate / "binary").write_bytes(content)
            (baseline / "binary").write_bytes(content)

            result = self.run_audit(
                "--root",
                str(candidate),
                "--allow-identical-baseline-root",
                str(baseline),
                "--private-marker",
                "private-marker",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("private-marker-1-in-content", result.stderr)

    def test_rejects_unexpected_private_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            key = (
                b"-----BEGIN "
                + b"PRIVATE KEY-----\n"
                + b"A" * 80
                + b"\n-----END "
                + b"PRIVATE KEY-----"
            )
            (root / "binary").write_bytes(key)

            result = self.run_audit("--root", str(root))

            self.assertEqual(result.returncode, 1)
            self.assertIn("embedded-private-key", result.stderr)

    def test_rejects_missing_requested_skip_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_audit(
                "--root",
                temporary,
                "--skip-path",
                "missing.tar.xz",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("requested-skip-path-not-found", result.stderr)


if __name__ == "__main__":
    unittest.main()
