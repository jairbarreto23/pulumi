"use strict";
require("dotenv").config();
const pulumi = require("@pulumi/pulumi");
const aws = require("@pulumi/aws");
const awsx = require("@pulumi/awsx");

const tags = {};

tags.Environment = pulumi.getStack();
tags.ProjectName = pulumi.getProject();
tags.StackName = pulumi.getStack();
tags.Team = "DA";

const publicHttpApiRouteKeys = [
  "GET /items",
  "PUT /items",
  "GET /items/{id}",
  "DELETE /items/{id}",
];

const publicHttpApiRoutes = [];

// DynamoDB item table
const itemsTable = new aws.dynamodb.Table("itemsTable", {
  attributes: [{ name: "id", type: "S" }],
  hashKey: "id",
  readCapacity: 1,
  writeCapacity: 1,
  tags: tags,
});

// Creating basic policy to grant permission to interact with DynamoDB
const itemsTableIamPolicy = new aws.iam.Policy("itemsTableIamPolicy", {
  description: "This policy grants permission to interact with DynamoDB",
  policy: itemsTable.arn.apply((itemsTableArn) =>
    JSON.stringify({
      Version: "2012-10-17",
      Statement: [
        {
          Action: [
            "dynamodb:DeleteItem",
            "dynamodb:GetItem",
            "dynamodb:PutItem",
            "dynamodb:Scan",
            "dynamodb:UpdateItem",
          ],
          Effect: "Allow",
          Resource: itemsTableArn,
        },
      ],
    })
  ),
  tags: tags,
});

// Creating Lambda Function role
const BasicBackendLambdaRole = new aws.iam.Role("BasicBackendLambdaRole", {
  assumeRolePolicy: JSON.stringify({
    Version: "2012-10-17",
    Statement: [
      {
        Action: "sts:AssumeRole",
        Effect: "Allow",
        Sid: "",
        Principal: {
          Service: "lambda.amazonaws.com",
        },
      },
    ],
  }),
  managedPolicyArns: [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    itemsTableIamPolicy.arn,
  ],
  tags: tags,
});

// Creating Lambda Function
const basicBackendCode = new pulumi.asset.AssetArchive({
  ".": new pulumi.asset.FileArchive("./src/lambda/basic-backend"),
});

const basicBackend = new aws.lambda.Function("basicBackend", {
  role: BasicBackendLambdaRole.arn,
  handler: "index.handler",
  runtime: aws.lambda.NodeJS12dXRuntime,
  code: basicBackendCode,
  tags: tags,
  environment: {
    variables: {
      DYNAMODB_TABLE: itemsTable.name,
    },
  },
});

// Creating API Gateway REST API
// let publicApi = new awsx.apigateway.API("publicApi", {
//   routes: [
//     {
//       path: "/items",
//       method: "GET",
//       eventHandler: aws.lambda.Function.get(
//         "basicBackendGetItems",
//         basicBackend.id
//       ),
//     },
//     {
//       path: "/items",
//       method: "PUT",
//       eventHandler: aws.lambda.Function.get(
//         "basicBackendPutItems",
//         basicBackend.id
//       ),
//     },
//     {
//       path: "/items/{id}",
//       method: "GET",
//       eventHandler: aws.lambda.Function.get(
//         "basicBackendGetItemsById",
//         basicBackend.id
//       ),
//     },
//     {
//       path: "/items/{id}",
//       method: "DELETE",
//       eventHandler: aws.lambda.Function.get(
//         "basicBackendDeleteItemsById",
//         basicBackend.id
//       ),
//     },
//   ],
// });

// Creating API Gateway HTTP API
const publicHttpApi = new aws.apigatewayv2.Api("publicHttpApi", {
  protocolType: "HTTP",
  description: "API Gateway using HTTP API",
  tags: tags,
});

const basicBackendPermission = new aws.lambda.Permission(
  "basicBackendPermission",
  {
    action: "lambda:InvokeFunction",
    principal: "apigateway.amazonaws.com",
    function: basicBackend,
    sourceArn: pulumi.interpolate`${publicHttpApi.executionArn}/*/*`,
    tags: tags,
  },
  { dependsOn: [publicHttpApi, basicBackend] }
);

const publicHttpApiIntegrationItemsRoute = new aws.apigatewayv2.Integration(
  "publicHttpApiIntegrationItemsRoute",
  {
    apiId: publicHttpApi.id,
    description: "Integration for basicBackend Lambda funtion",
    integrationType: "AWS_PROXY",
    integrationUri: basicBackend.arn,
    payloadFormatVersion: "1.0", // default 1.0, it can 2.0, the lambda function has to expect the correspond payload format.
    integrationMethod: "ANY",
  }
);

publicHttpApiRouteKeys.forEach((item) => {
  let routeName = item.replace(/[^A-Z0-9]/gi, "");
  publicHttpApiRoutes.push(
    new aws.apigatewayv2.Route(routeName, {
      apiId: publicHttpApi.id,
      routeKey: item,
      target: pulumi.interpolate`integrations/${publicHttpApiIntegrationItemsRoute.id}`,
    })
  );
});

const publicHttpApiDefaultStage = new aws.apigatewayv2.Stage(
  "publicHttpApiDefaultStage",
  {
    apiId: publicHttpApi.id,
    name: pulumi.getStack(),
    autoDeploy: true,
    tags: tags,
  },
  {
    dependsOn: publicHttpApiRoutes,
  }
);

// Create an AWS resource (S3 Bucket)
// const buckets = [];
// if (process.env.CREATE_BUCKETS === "true") {
//   [1].forEach((i) => {
//     buckets.push(
//       new aws.s3.Bucket("my-bucket" + i, {
//         tags: tags,
//       })
//     );
//   });
// }

// Outputs utilities
// const bucketsId = [];
// for (const bucket of buckets) {
//   bucketsId.push(bucket.id);
// }

// Export the name of the bucket
// exports.bucketsName = bucketsId;
// exports.projectName = pulumi.getProject();
// exports.RestApiUrl = publicApi.url;
exports.HttpApiDevUrl = publicHttpApiDefaultStage.invokeUrl;
