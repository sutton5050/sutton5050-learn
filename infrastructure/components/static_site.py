from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
)
from constructs import Construct


class StaticSite(Construct):
    """Reusable construct: static files served via S3 + CloudFront."""

    def __init__(self, scope: Construct, id: str, *,
                 source_path: str):
        super().__init__(scope, id)

        bucket = s3.Bucket(
            self, "Bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        self.distribution = cloudfront.Distribution(
            self, "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
        )

        s3deploy.BucketDeployment(
            self, "Deploy",
            sources=[s3deploy.Source.asset(source_path)],
            destination_bucket=bucket,
            distribution=self.distribution,
            distribution_paths=["/*"],
        )
