from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
    RemovalPolicy,
)
from constructs import Construct


class StaticSite(Construct):
    """Reusable construct: static files served via S3 + CloudFront."""

    def __init__(self, scope: Construct, id: str, *,
                 source_path: str,
                 domain_names: list = None,
                 certificate_arn: str = None,
                 hosted_zone_id: str = None,
                 hosted_zone_name: str = None):
        super().__init__(scope, id)

        bucket = s3.Bucket(
            self, "Bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        certificate = (
            acm.Certificate.from_certificate_arn(self, "Certificate", certificate_arn)
            if certificate_arn else None
        )

        self.distribution = cloudfront.Distribution(
            self, "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
            domain_names=domain_names or [],
            certificate=certificate,
        )

        s3deploy.BucketDeployment(
            self, "Deploy",
            sources=[s3deploy.Source.asset(source_path)],
            destination_bucket=bucket,
            distribution=self.distribution,
            distribution_paths=["/*"],
        )

        if hosted_zone_id and hosted_zone_name and domain_names:
            zone = route53.HostedZone.from_hosted_zone_attributes(
                self, "Zone",
                hosted_zone_id=hosted_zone_id,
                zone_name=hosted_zone_name,
            )
            for domain in domain_names:
                record_id = domain.replace(".", "").replace("www", "Www")
                route53.ARecord(
                    self, f"ARecord{record_id}",
                    zone=zone,
                    record_name=domain,
                    target=route53.RecordTarget.from_alias(
                        targets.CloudFrontTarget(self.distribution)
                    ),
                )
