import aws_cdk as cdk
from constructs import Construct
from components.static_site import StaticSite


class FrontendStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        StaticSite(
            self, "Dashboard",
            source_path="../frontend",
            domain_names=["sutton5050.com", "www.sutton5050.com"],
            certificate_arn="arn:aws:acm:us-east-1:902672427642:certificate/60d70fbe-d2d5-4417-9e90-aafc4958cc56",
            hosted_zone_id="Z03151509FL1UXA4XHI7",
            hosted_zone_name="sutton5050.com",
        )
