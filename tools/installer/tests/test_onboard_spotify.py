from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "onboard_spotify.py"
SPEC = importlib.util.spec_from_file_location("onboard_spotify", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
ONBOARDING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ONBOARDING)


def credential_value() -> dict[str, object]:
    return {
        "username": "private-test-account",
        "auth_type": 1,
        "auth_data": base64.b64encode(b"x" * 32).decode("ascii"),
    }


class CredentialValidationTests(unittest.TestCase):
    def write_value(self, directory: Path, value: object) -> Path:
        path = directory / "credentials.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        path.chmod(0o600)
        return path

    def test_accepts_reusable_librespot_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_value(Path(temporary), credential_value())
            ONBOARDING.validate_credentials(path)

    def test_rejects_missing_reusable_username(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            value = credential_value()
            value["username"] = None
            path = self.write_value(Path(temporary), value)
            with self.assertRaises(ONBOARDING.OnboardingError):
                ONBOARDING.validate_credentials(path)

    def test_rejects_invalid_base64(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            value = credential_value()
            value["auth_data"] = "not base64!"
            path = self.write_value(Path(temporary), value)
            with self.assertRaises(ONBOARDING.OnboardingError):
                ONBOARDING.validate_credentials(path)

    def test_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self.write_value(directory, credential_value())
            link = directory / "credentials-link.json"
            link.symlink_to(source)
            with self.assertRaises(ONBOARDING.OnboardingError):
                ONBOARDING.validate_credentials(link)

    def test_rejects_readable_by_other_users(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_value(Path(temporary), credential_value())
            path.chmod(0o644)
            with self.assertRaises(ONBOARDING.OnboardingError):
                ONBOARDING.validate_credentials(path)


if __name__ == "__main__":
    unittest.main()
