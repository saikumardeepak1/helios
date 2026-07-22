import pytest

from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip() -> None:
    token = create_access_token("user-123")
    assert decode_token(token, TokenType.ACCESS) == "user-123"


def test_refresh_token_roundtrip() -> None:
    token = create_refresh_token("user-123")
    assert decode_token(token, TokenType.REFRESH) == "user-123"


def test_access_token_rejected_as_refresh_token() -> None:
    token = create_access_token("user-123")
    with pytest.raises(InvalidTokenError):
        decode_token(token, TokenType.REFRESH)


def test_garbage_token_raises_invalid_token_error() -> None:
    with pytest.raises(InvalidTokenError):
        decode_token("not-a-real-token", TokenType.ACCESS)


def test_generate_api_key_returns_prefix_and_verifiable_hash() -> None:
    raw_key, prefix, hashed_key = generate_api_key()

    assert raw_key.startswith("hel_live_")
    assert prefix == raw_key[: len(prefix)]
    assert hash_api_key(raw_key) == hashed_key


def test_generate_api_key_is_unique_each_call() -> None:
    first_raw, _, _ = generate_api_key()
    second_raw, _, _ = generate_api_key()
    assert first_raw != second_raw
