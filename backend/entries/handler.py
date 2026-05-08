import json
import os
import time
import uuid

import boto3
from boto3.dynamodb.conditions import Key

from shared.auth_utils import get_jwt_secret, verify_jwt

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Content-Type": "application/json",
}


def resp(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": CORS, "body": json.dumps(body)}


def require_auth(event) -> tuple:
    """Returns (payload, None) on success or (None, error_response) on failure."""
    auth_header = (event.get("headers") or {}).get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, resp(401, {"error": "Missing or invalid Authorization header"})
    token = auth_header[7:]
    try:
        payload = verify_jwt(token, get_jwt_secret())
        return payload, None
    except ValueError as e:
        return None, resp(401, {"error": str(e)})


def lambda_handler(event, context):
    _, err = require_auth(event)
    if err:
        return err

    route = event.get("routeKey", "")

    if route == "GET /entries":
        return handle_list()

    if route == "POST /entries":
        body = json.loads(event.get("body") or "{}")
        return handle_create(body)

    if route == "DELETE /entries/{id}":
        entry_id = (event.get("pathParameters") or {}).get("id")
        return handle_delete(entry_id)

    return resp(404, {"error": "Not found"})


def handle_list():
    try:
        result = table.query(KeyConditionExpression=Key("PK").eq("ENTRY"))
        items = result.get("Items", [])
        entries = [
            {
                "id": item["SK"],
                "encrypted_data": item["encrypted_data"],
                "iv": item["iv"],
                "created_at": item.get("created_at", ""),
            }
            for item in sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)
        ]
        return resp(200, {"entries": entries})
    except Exception as e:
        return resp(500, {"error": str(e)})


def handle_create(body: dict):
    try:
        encrypted_data = body.get("encrypted_data")
        iv = body.get("iv")
        if not encrypted_data or not iv:
            return resp(400, {"error": "Missing encrypted_data or iv"})

        entry_id = str(uuid.uuid4())
        table.put_item(
            Item={
                "PK": "ENTRY",
                "SK": entry_id,
                "encrypted_data": encrypted_data,
                "iv": iv,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        return resp(201, {"id": entry_id})
    except Exception as e:
        return resp(500, {"error": str(e)})


def handle_delete(entry_id: str):
    try:
        if not entry_id:
            return resp(400, {"error": "Missing entry ID"})
        table.delete_item(Key={"PK": "ENTRY", "SK": entry_id})
        return resp(200, {"deleted": True})
    except Exception as e:
        return resp(500, {"error": str(e)})
