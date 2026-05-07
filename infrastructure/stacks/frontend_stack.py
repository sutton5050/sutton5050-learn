import aws_cdk as cdk
from constructs import Construct
from components.static_site import StaticSite


class FrontendStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        StaticSite(
            self, "Dashboard",
            source_path="../frontend",
        )
