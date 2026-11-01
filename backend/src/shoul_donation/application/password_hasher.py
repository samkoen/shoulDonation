"""Password hashing with PBKDF2. The iteration count is stored inside the hash."""

import hashlib
import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import Error as BinaryDecodeError


class PasswordHasher:
    _PREFIX = "pbkdf2_sha256"

    def __init__(self, iterations: int) -> None:
        if iterations < 1:
            raise ValueError("iterations must be positive")
        self._iterations = iterations

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = self._digest(password, salt, self._iterations)
        return self._format(self._iterations, salt, digest)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            iterations, salt, expected = self._parse(password_hash)
        except (ValueError, BinaryDecodeError):
            return False
        actual = self._digest(password, salt, iterations)
        return secrets.compare_digest(actual, expected)

    def _digest(self, password: str, salt: bytes, iterations: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)

    def _format(self, iterations: int, salt: bytes, digest: bytes) -> str:
        salt_text = urlsafe_b64encode(salt).decode("ascii")
        digest_text = urlsafe_b64encode(digest).decode("ascii")
        return f"{self._PREFIX}${iterations}${salt_text}${digest_text}"

    def _parse(self, password_hash: str) -> tuple[int, bytes, bytes]:
        prefix, iterations, salt_text, digest_text = password_hash.split("$")
        if prefix != self._PREFIX:
            raise ValueError("unsupported hash")
        return int(iterations), urlsafe_b64decode(salt_text), urlsafe_b64decode(digest_text)
