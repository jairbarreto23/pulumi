const AWS = require("aws-sdk");

const dynamo = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event, context) => {
  let dynamoDbTable = process.env.DYNAMODB_TABLE;
  let body;
  let statusCode = 200;
  const headers = {
    "Content-Type": "application/json",
  };
  const routeKey = event.httpMethod + " " + event.resource;

  try {
    switch (routeKey) {
      case "DELETE /items/{id}":
        await dynamo
          .delete({
            TableName: dynamoDbTable,
            Key: {
              id: event.pathParameters.id,
            },
          })
          .promise();
        body = `Deleted item ${event.pathParameters.id}`;
        break;
      case "GET /items/{id}":
        body = await dynamo
          .get({
            TableName: dynamoDbTable,
            Key: {
              id: event.pathParameters.id,
            },
          })
          .promise();
        break;
      case "GET /items":
        body = await dynamo.scan({ TableName: dynamoDbTable }).promise();
        break;
      case "PUT /items":
        let requestJSON;
        if (event.isBase64Encoded == true) {
          let buff = Buffer.from(event.body, "base64");
          let eventBodyStr = buff.toString("UTF-8");
          requestJSON = JSON.parse(eventBodyStr);
        } else {
          requestJSON = JSON.parse(event.body);
        }
        await dynamo
          .put({
            TableName: dynamoDbTable,
            Item: {
              id: requestJSON.id,
              price: requestJSON.price,
              name: requestJSON.name,
            },
          })
          .promise();
        body = `Put item ${requestJSON.id}`;
        break;
      default:
        throw new Error(`Unsupported route: "${routeKey}"`);
    }
  } catch (err) {
    statusCode = 400;
    body = err.message;
  } finally {
    body = JSON.stringify(body);
  }

  return {
    statusCode,
    body,
    headers,
  };
};
