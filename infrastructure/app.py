import aws_cdk as cdk
from stacks.frontend_stack import FrontendStack
from stacks.backend_stack import BackendStack

app = cdk.App()

env = cdk.Environment(account="902672427642", region="eu-west-2")

BackendStack(app, "Sutton5050Backend", env=env)
FrontendStack(app, "Sutton5050Frontend", env=env)

app.synth()
