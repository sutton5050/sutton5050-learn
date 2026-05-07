from aws_cdk import (
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    Duration,
)
from constructs import Construct


class ApiLambda(Construct):
    """Reusable construct: a Lambda function exposed via API Gateway."""

    def __init__(self, scope: Construct, id: str, *,
                 code_path: str,
                 handler: str,
                 environment: dict = None):
        super().__init__(scope, id)

        self.function = lambda_.Function(
            self, "Function",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler=handler,
            code=lambda_.Code.from_asset(code_path),
            environment=environment or {},
            timeout=Duration.seconds(10),
        )

        self.api = apigw.LambdaRestApi(
            self, "Api",
            handler=self.function,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET"],
            ),
        )

        self.url = self.api.url
