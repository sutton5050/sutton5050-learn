import base64
import hashlib
import hmac
import json
import os
import time

import boto3

_jwt_secret_cache = None


def get_jwt_secret() -> str:
    global _jwt_secret_cache
    if _jwt_secret_cache is None:
        ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION", "eu-west-2"))
        param = ssm.get_parameter(
            Name=os.environ["JWT_SECRET_PARAM"],
            WithDecryption=True,
        )
        _jwt_secret_cache = param["Parameter"]["Value"]
    return _jwt_secret_cache


# ── JWT (stdlib only, no external deps) ────────────────────────────────────

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = (4 - len(s) % 4) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)


def create_jwt(payload: dict, secret: str) -> str:
    header = _b64url_encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()
    )
    body = _b64url_encode(
        json.dumps(payload, separators=(",", ":")).encode()
    )
    sig = hmac.new(
        secret.encode(),
        f"{header}.{body}".encode(),
        hashlib.sha256,
    ).digest()
    return f"{header}.{body}.{_b64url_encode(sig)}"


def verify_jwt(token: str, secret: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header, body, sig = parts
    expected = hmac.new(
        secret.encode(),
        f"{header}.{body}".encode(),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(_b64url_encode(expected), sig):
        raise ValueError("Invalid token signature")

    payload = json.loads(_b64url_decode(body))
    if payload.get("exp", 0) < time.time():
        raise ValueError("Token expired")

    return payload
