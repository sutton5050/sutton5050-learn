import aws_cdk as cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
)
from constructs import Construct


class FrontendStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # ── S3 bucket ───────────────────────────────────────────────
        bucket = s3.Bucket(
            self, "Bucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ── ACM cert (us-east-1 for CloudFront) ────────────────────
        cert = acm.Certificate.from_certificate_arn(
            self, "Certificate",
            "arn:aws:acm:us-east-1:902672427642:certificate/60d70fbe-d2d5-4417-9e90-aafc4958cc56",
        )

        # ── CloudFront ──────────────────────────────────────────────
        distribution = cloudfront.Distribution(
            self, "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
            ),
            domain_names=["sutton5050.com", "www.sutton5050.com"],
            certificate=cert,
            default_root_object="index.html",
        )

        # ── Deploy frontend ─────────────────────────────────────────
        s3deploy.BucketDeployment(
            self, "Deploy",
            sources=[s3deploy.Source.asset("../frontend")],
            destination_bucket=bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        # ── Route53 ─────────────────────────────────────────────────
        zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "Zone",
            hosted_zone_id="Z03151509FL1UXA4XHI7",
            zone_name="sutton5050.com",
        )

        route53.ARecord(
            self, "ARecord",
            zone=zone,
            record_name="sutton5050.com",
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution)
            ),
        )

        route53.ARecord(
            self, "WwwARecord",
            zone=zone,
            record_name="www.sutton5050.com",
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution)
            ),
        )
