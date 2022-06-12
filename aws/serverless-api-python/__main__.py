"""An AWS Python Pulumi program"""

import json
import re
import pulumi
import pulumi_aws as aws

publicHttpApiRouteKeys = [
    "GET /items",
    "PUT /items",
    "GET /items/{id}",
    "DELETE /items/{id}",
]

publicHttpApiRoutes = []

tags = {
    "Environment": pulumi.get_stack(),
    "ProjectName": pulumi.get_project(),
    "StackName": pulumi.get_stack(),
    "Team": "DA",
}

# DynamoDB item table
itemsTable = aws.dynamodb.Table(
    "itemsTable",
    attributes=[aws.dynamodb.TableAttributeArgs(name="id", type="S")],
    hash_key="id",
    read_capacity=1,
    write_capacity=1,
    tags=tags,
)

itemsTableIamPolicy = aws.iam.Policy(
    "itemsTableIamPolicy",
    description="This policy grants permission to interact with DynamoDB",
    policy=itemsTable.arn.apply(
        lambda arn: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:DeleteItem",
                            "dynamodb:GetItem",
                            "dynamodb:PutItem",
                            "dynamodb:Scan",
                            "dynamodb:UpdateItem",
                        ],
                        "Resource": arn,
                    }
                ],
            }
        )
    ),
    tags=tags,
)

# Creating Lambda Function role
dynamoDbCrudLambdaRole = aws.iam.Role(
    "dynamoDbCrudLambdaRole",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Sid": "",
                    "Principal": {
                        "Service": "lambda.amazonaws.com",
                    },
                },
            ],
        }
    ),
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        itemsTableIamPolicy.arn,
    ],
    tags=tags,
)

# Creating Lambda Function
dynamoDbCrudLambdaCode = pulumi.asset.AssetArchive(
    {
        ".": pulumi.asset.FileArchive("./src/lambda/dynamodb-crud"),
    }
)

dynamoDbCrudLambda = aws.lambda_.Function(
    "dynamoDbCrudLambda",
    role=dynamoDbCrudLambdaRole.arn,
    handler="index.handler",
    runtime=aws.lambda_.Runtime.NODE_JS14D_X,
    code=dynamoDbCrudLambdaCode,
    tags=tags,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={"DYNAMODB_TABLE": itemsTable.name}
    ),
)

# Creating API Authorizer role
apiAuthorizerRole = aws.iam.Role(
    "apiAuthorizerRole",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Sid": "",
                    "Principal": {
                        "Service": "lambda.amazonaws.com",
                    },
                },
            ],
        }
    ),
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    ],
    tags=tags,
)

# Creating API Authorizer
apiAuthorizerCode = pulumi.asset.AssetArchive(
    {
        ".": pulumi.asset.FileArchive("./src/lambda/authorizer"),
    }
)

apiAuthorizerLambda = aws.lambda_.Function(
    "apiAuthorizerLambda",
    role=apiAuthorizerRole.arn,
    handler="index.handler",
    runtime=aws.lambda_.Runtime.NODE_JS14D_X,
    code=apiAuthorizerCode,
    tags=tags,
)

# Creating API Gateway HTTP API
publicHttpApi = aws.apigatewayv2.Api(
    "publicHttpApi",
    protocol_type="HTTP",
    description="API Gateway using HTTP API",
    tags=tags,
)

# Creating Custom Authorizer
publicHttpApiAuthorizer = aws.apigatewayv2.Authorizer(
    "publicHttpApiAuthorizer",
    api_id=publicHttpApi.id,
    authorizer_type="REQUEST",
    authorizer_uri=apiAuthorizerLambda.invoke_arn,
    identity_sources=["$request.header.authorizationToken"],
    authorizer_payload_format_version="1.0",
    authorizer_result_ttl_in_seconds=0,
)

# Permissions to API Gateway to invoke the lambda function
dynamoDbCrudLambdaPermissions = aws.lambda_.Permission(
    "dynamoDbCrudLambdaPermissions",
    action="lambda:InvokeFunction",
    principal="apigateway.amazonaws.com",
    function=dynamoDbCrudLambda.arn,
    source_arn=pulumi.Output.concat(publicHttpApi.execution_arn, "/*/*"),
    opts=pulumi.ResourceOptions(depends_on=[publicHttpApi, dynamoDbCrudLambda]),
)

# Permissions to API Gateway to invoke Custom Authorizer
apiAuthorizerLambdaPermissions = aws.lambda_.Permission(
    "apiAuthorizerLambdaPermissions",
    action="lambda:InvokeFunction",
    principal="apigateway.amazonaws.com",
    function=apiAuthorizerLambda.arn,
    source_arn=pulumi.Output.concat(
        publicHttpApi.execution_arn, "/authorizers/", publicHttpApiAuthorizer.id
    ),
    opts=pulumi.ResourceOptions(
        depends_on=[publicHttpApi, apiAuthorizerLambda, publicHttpApiAuthorizer]
    ),
)

# Creating the lambda function integration
publicHttpApiIntegrationItemsRoute = aws.apigatewayv2.Integration(
    "publicHttpApiIntegrationItemsRoute",
    api_id=publicHttpApi.id,
    description="Integration for basicBackend Lambda funtion",
    integration_type="AWS_PROXY",
    integration_uri=dynamoDbCrudLambda.invoke_arn,
    payload_format_version="1.0",
)

# Creating routes
for item in publicHttpApiRouteKeys:
    routeName = re.sub("[^a-zA-Z0-9]", "", item)
    publicHttpApiRoutes.append(
        aws.apigatewayv2.Route(
            routeName,
            authorization_type="CUSTOM",
            authorizer_id=publicHttpApiAuthorizer.id,
            api_id=publicHttpApi.id,
            route_key=item,
            target=pulumi.Output.concat(
                "integrations/", publicHttpApiIntegrationItemsRoute.id
            ),
        )
    )

# Creating default stage
publicHttpApiDefaultStage = aws.apigatewayv2.Stage(
    "publicHttpApiDefaultStage",
    api_id=publicHttpApi.id,
    name=pulumi.get_stack(),
    auto_deploy=True,
    tags=tags,
    opts=pulumi.ResourceOptions(depends_on=publicHttpApiRoutes),
)

# Outputs
pulumi.export(name="dynamoDbCrudLambda", value=dynamoDbCrudLambda.name)
pulumi.export(
    name="publicHttpApiDefaultStage", value=publicHttpApiDefaultStage.invoke_url
)
