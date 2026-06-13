from app.services.auth import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hashing() -> None:
    password = "supersecretpassword123"
    hashed = hash_password(password)
    
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
    assert verify_password(password, "invalid_hash_string") is False


def test_jwt_token_handling() -> None:
    data = {"sub": "user-123", "username": "student_test"}
    token = create_access_token(data)
    
    assert isinstance(token, str)
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-123"
    assert decoded["username"] == "student_test"
    assert "exp" in decoded


def test_invalid_jwt_handling() -> None:
    assert decode_access_token("this.is.an.invalid.token") is None
    assert decode_access_token("") is None
