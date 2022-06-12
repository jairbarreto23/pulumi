"""An Azure RM Python Pulumi program"""

import pulumi
import pulumi_azure_native as az
from pulumi_azure_native import storage
from pulumi_azure_native import resources

resourceGroupId = "/subscriptions/0bea0a37-89cb-43fb-976f-0d8a3d8b1e4b/resourceGroups/celula-devopscloud"
resourceGroupName = "celula-devopscloud"

tags = {
    "Owner": "Andres Gomez",
    "Environment": pulumi.get_stack(),
    "ProjectName": pulumi.get_project(),
    "StackName": pulumi.get_stack(),
    "Team": "DA",
}

# Create an Azure Resource Group
# resource_group = resources.ResourceGroup(
#     "resource_group",
#     resource_group_name="celula-devopscloud",
#     opts=pulumi.ResourceOptions(import_=resourceGroupId),
# )

# Create an Azure resource (Storage Account)
account = storage.StorageAccount(
    "sa",
    resource_group_name=resourceGroupName,
    sku=storage.SkuArgs(
        name=storage.SkuName.STANDARD_LRS,
    ),
    kind=storage.Kind.STORAGE_V2,
)

# Enable static website support
static_website = storage.StorageAccountStaticWebsite(
    "staticWebsite",
    account_name=account.name,
    resource_group_name=resourceGroupName,
    index_document="index.html",
)

# Upload the file
index_html = storage.Blob(
    "index.html",
    resource_group_name=resourceGroupName,
    account_name=account.name,
    container_name=static_website.container_name,
    source=pulumi.FileAsset("index.html"),
    content_type="text/html",
)

# Export the primary key of the Storage Account
primary_key = (
    pulumi.Output.all(resourceGroupName, account.name)
    .apply(
        lambda args: storage.list_storage_account_keys(
            resource_group_name=args[0], account_name=args[1]
        )
    )
    .apply(lambda accountKeys: accountKeys.keys[0].value)
)

pulumi.export("primary_storage_key", primary_key)
# Web endpoint to the website
pulumi.export("staticEndpoint", account.primary_endpoints.web)
