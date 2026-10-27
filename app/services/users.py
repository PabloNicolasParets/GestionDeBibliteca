import hashlib
import hmac
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

DEFAULT_USERS = {
    "usuario": ("usuario", "usuario"),
    "administrador": ("administrador", "administrador"),
}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=len(expected)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(
        select(User).where(User.username == username.strip().lower())
    )
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def ensure_default_users(db: Session) -> None:
    for user in db.scalars(select(User)).all():
        if user.username not in DEFAULT_USERS:
            db.delete(user)

    for username, (password, role) in DEFAULT_USERS.items():
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            db.add(
                User(
                    username=username,
                    password_hash=hash_password(password),
                    role=role,
                )
            )
        else:
            user.role = role
            if not verify_password(password, user.password_hash):
                user.password_hash = hash_password(password)
    db.commit()
