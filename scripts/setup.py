"""
Run this ONCE after your first CDK deploy to set your master password
and generate the JWT secret.

Usage:
    cd sutton5050-web
    python scripts/setup.py
"""

import hashlib
import os
import secrets
import sys

import boto3

AWS_REGION = "eu-west-2"
BACKEND_STACK = "PasswordManagerBackend"
JWT_SECRET_PARAM = "/password-manager/jwt-secret"


def get_table_name() -> str:
    cf = boto3.client("cloudformation", region_name=AWS_REGION)
    stacks = cf.describe_stacks(StackName=BACKEND_STACK)["Stacks"]
    for output in stacks[0].get("Outputs", []):
        if output["OutputKey"] == "TableName":
            return output["OutputValue"]
    raise RuntimeError("TableName output not found in CloudFormation stack")


def derive_verification_hash(password: str) -> str:
    """Mirror of the browser's PBKDF2 derivation — must match frontend exactly."""
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        b"verification-salt-v1",
        600000,
    )
    return dk.hex()


def main():
    print("=" * 50)
    print("  Password Manager — First-time Setup")
    print("=" * 50)
    print()

    # Master password
    password = input("Enter your master password: ").strip()
    if len(password) < 8:
        print("Error: Password must be at least 8 characters.")
        sys.exit(1)

    confirm = input("Confirm master password: ").strip()
    if password != confirm:
        print("Error: Passwords do not match.")
        sys.exit(1)

    print("\nWorking...")

    # Derive values
    verification_hash = derive_verification_hash(password)
    encryption_salt = secrets.token_hex(32)   # 256-bit random salt
    jwt_secret = secrets.token_hex(32)        # 256-bit random JWT secret

    # Get DynamoDB table name from CloudFormation
    try:
        table_name = get_table_name()
        print(f"Found DynamoDB table: {table_name}")
    except Exception as e:
        print(f"Warning: could not auto-detect table name ({e})")
        table_name = input("Enter DynamoDB table name manually: ").strip()

    # Write config to DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(table_name)
    table.put_item(
        Item={
            "PK": "CONFIG",
            "SK": "CONFIG",
            "verification_hash": verification_hash,
            "encryption_salt": encryption_salt,
        }
    )
    print("✓ Master password stored in DynamoDB")

    # Write JWT secret to SSM Parameter Store
    ssm = boto3.client("ssm", region_name=AWS_REGION)
    ssm.put_parameter(
        Name=JWT_SECRET_PARAM,
        Value=jwt_secret,
        Type="SecureString",
        Overwrite=True,
    )
    print("✓ JWT secret stored in SSM Parameter Store")

    print()
    print("Setup complete! You can now log in at https://sutton5050.com")
    print()
    print("To change your master password in future, just re-run this script.")


if __name__ == "__main__":
    main()
