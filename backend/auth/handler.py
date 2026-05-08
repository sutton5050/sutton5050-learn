import hashlib
import hmac
import json
import os
import time

import boto3

from shared.auth_utils import create_jwt, get_jwt_secret

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Content-Type": "application/json",
}


def resp(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": CORS, "body": json.dumps(body)}


def lambda_handler(event, context):
    route = event.get("routeKey", "")

    if route == "GET /auth/config":
        return handle_config()

    if route == "POST /auth/login":
        body = json.loads(event.get("body") or "{}")
        return handle_login(body)

    return resp(404, {"error": "Not found"})


def handle_config():
    try:
        result = table.get_item(Key={"PK": "CONFIG", "SK": "CONFIG"})
        item = result.get("Item")
        if not item:
            return resp(503, {"error": "App not configured — run scripts/setup.py"})
        return resp(200, {"encryption_salt": item["encryption_salt"]})
    except Exception as e:
        return resp(500, {"error": str(e)})


def handle_login(body: dict):
    try:
        incoming_hash = body.get("verification_hash", "")
        if not incoming_hash:
            return resp(400, {"error": "Missing verification_hash"})

        result = table.get_item(Key={"PK": "CONFIG", "SK": "CONFIG"})
        item = result.get("Item")
        if not item:
            return resp(503, {"error": "App not configured — run scripts/setup.py"})

        stored_hash = item.get("verification_hash", "")

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(incoming_hash.lower(), stored_hash.lower()):
            return resp(401, {"error": "Invalid password"})

        secret = get_jwt_secret()
        token = create_jwt(
            {
                "sub": "owner",
                "iat": int(time.time()),
                "exp": int(time.time()) + 8 * 3600,  # 8-hour session
            },
            secret,
        )
        return resp(200, {"token": token})

    except Exception as e:
        return resp(500, {"error": str(e)})
