import os
from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ALGORITHM = "HS256"

def get_secret_key() -> str:
    return os.getenv("SECRET_KEY", "dev-secret-change-me")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(sub: str, expires_minutes: int) -> str:
    exp = datetime.utcnow() + timedelta(minutes=expires_minutes)
    token = jwt.encode({"sub": sub, "exp": exp}, get_secret_key(), algorithm=ALGORITHM)
    # PyJWT bazen bytes döndürebilir, str'e çevir
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        return str(payload["sub"])
    except jwt.PyJWTError as e:
        raise ValueError("Invalid token") from e
