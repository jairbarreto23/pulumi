# Serverless API

Se utiliza como base el tutorial [Tutorial: Build a CRUD API with Lambda and DynamoDB](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-dynamo-db.html#http-api-dynamo-db-create-table) para crear una estructura de API serverless en AWS.

## Requerimientos

- [Pulumi](https://www.pulumi.com/docs/get-started/install/)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- AWS CLI [configurado](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) con credenciales.

## Referencias

- [Pulumi Node.js SDK](https://www.pulumi.com/docs/reference/pkg/nodejs/pulumi/pulumi/)
- [AWS Classic Packages](https://www.pulumi.com/registry/packages/aws/api-docs/)
- [pulumi/awsx](https://www.pulumi.com/docs/reference/pkg/nodejs/pulumi/awsx/apigateway/)

## Configurar acceso a cuenta AWS

### Mediante CLI

```sh
$aws configure
AWS Access Key ID [None]: <YOUR_ACCESS_KEY_ID>
AWS Secret Access Key [None]: <YOUR_SECRET_ACCESS_KEY>
Default region name [None]:
Default output format [None]:
```

### Mediante variables de entorno Windows

```sh
$env:AWS_ACCESS_KEY_ID = "<YOUR_ACCESS_KEY_ID>"
$env:AWS_SECRET_ACCESS_KEY = "<YOUR_SECRET_ACCESS_KEY>"   
```
