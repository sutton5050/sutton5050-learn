import aws_cdk as cdk
from stacks.backend_stack import BackendStack
from stacks.frontend_stack import FrontendStack

app = cdk.App()

env = cdk.Environment(account="902672427642", region="eu-west-2")

BackendStack(app, "PasswordManagerBackend", env=env)
FrontendStack(app, "PasswordManagerFrontend", env=env)

app.synth()
