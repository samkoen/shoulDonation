"""Password hashing."""

from shoul_donation.application.password_hasher import PasswordHasher


def test_hash_verifies_the_same_password_only() -> None:
    hasher = PasswordHasher(iterations=1_000)
    stored = hasher.hash("correct-horse")
    assert stored != "correct-horse"
    assert hasher.verify("correct-horse", stored)
    assert not hasher.verify("other-horse", stored)


def test_malformed_hash_is_rejected() -> None:
    hasher = PasswordHasher(iterations=1_000)
    assert not hasher.verify("correct-horse", "not-a-hash")
