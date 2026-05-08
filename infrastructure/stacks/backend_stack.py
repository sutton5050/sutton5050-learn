import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_iam as iam,
)
from constructs import Construct


class BackendStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # ── DynamoDB ────────────────────────────────────────────────
        table = dynamodb.Table(
            self, "Table",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.RETAIN,  # Never auto-delete vault data
        )

        shared_env = {
            "TABLE_NAME": table.table_name,
            "JWT_SECRET_PARAM": "/password-manager/jwt-secret",
        }

        # ── Lambda functions ────────────────────────────────────────
        auth_fn = lambda_.Function(
            self, "AuthFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("../backend"),
            handler="auth.handler.lambda_handler",
            environment=shared_env,
            timeout=cdk.Duration.seconds(15),
        )

        entries_fn = lambda_.Function(
            self, "EntriesFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("../backend"),
            handler="entries.handler.lambda_handler",
            environment=shared_env,
            timeout=cdk.Duration.seconds(15),
        )

        # ── Permissions ─────────────────────────────────────────────
        table.grant_read_write_data(auth_fn)
        table.grant_read_write_data(entries_fn)

        ssm_policy = iam.PolicyStatement(
            actions=["ssm:GetParameter"],
            resources=[
                f"arn:aws:ssm:{self.region}:{self.account}:parameter/password-manager/jwt-secret"
            ],
        )
        auth_fn.add_to_role_policy(ssm_policy)
        entries_fn.add_to_role_policy(ssm_policy)

        # ── HTTP API Gateway ────────────────────────────────────────
        api = apigwv2.HttpApi(
            self, "Api",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigwv2.CorsHttpMethod.ANY],
                allow_headers=["Content-Type", "Authorization"],
            ),
        )

        auth_int = integrations.HttpLambdaIntegration("AuthInt", auth_fn)
        entries_int = integrations.HttpLambdaIntegration("EntriesInt", entries_fn)

        api.add_routes(
            path="/auth/config",
            methods=[apigwv2.HttpMethod.GET],
            integration=auth_int,
        )
        api.add_routes(
            path="/auth/login",
            methods=[apigwv2.HttpMethod.POST],
            integration=auth_int,
        )
        api.add_routes(
            path="/entries",
            methods=[apigwv2.HttpMethod.GET, apigwv2.HttpMethod.POST],
            integration=entries_int,
        )
        api.add_routes(
            path="/entries/{id}",
            methods=[apigwv2.HttpMethod.DELETE],
            integration=entries_int,
        )

        # ── Outputs ─────────────────────────────────────────────────
        self.api_url = api.url
        cdk.CfnOutput(self, "ApiUrl", value=api.url)
        cdk.CfnOutput(self, "TableName", value=table.table_name)
