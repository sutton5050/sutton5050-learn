import aws_cdk as cdk
from constructs import Construct
from components.api_lambda import ApiLambda


class BackendStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        ApiLambda(
            self, "FootballApi",
            code_path="../backend",
            handler="lambda_function.lambda_handler",
            environment={
                "FOOTBALL_API_KEY": "65de886ae48c45cfbe8f8d3a9af7fbc4",
            },
        )
