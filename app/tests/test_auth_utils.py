import bcrypt

from app.utils.auth import hash_password, verify_password


def test_hash_password_supports_long_passwords():
    password = "p" * 100

    password_hash = hash_password(password)

    assert verify_password(password, password_hash)


def test_verify_password_supports_existing_bcrypt_hashes():
    password = "legacy-password"
    legacy_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    assert verify_password(password, legacy_hash)


def test_verify_password_rejects_wrong_password():
    password_hash = hash_password("correct-password")

    assert not verify_password("wrong-password", password_hash)


