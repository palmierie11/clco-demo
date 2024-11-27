"""An Azure RM Python Pulumi program"""
# link to github https://github.com/palmierie11/clco-demo
import pulumi
from pulumi import AssetArchive, FileAsset
from pulumi_azure_native import resources, storage, web

# Create an Azure Resource Group
resource_group = resources.ResourceGroup("ResourceGroup2")

# Create a Storage Account
storage_account = storage.StorageAccount(
    "storaccount2",
    resource_group_name=resource_group.name,
    sku=storage.SkuArgs(name="Standard_LRS"),
    kind="StorageV2",
    location="EastUS"
)

# Package a local directory into an archive
app_archive = AssetArchive({
    ".": FileAsset("./app.py")
})

# Create a Blob Container
blob_container = storage.BlobContainer(
    "blobcontainer",
    resource_group_name=resource_group.name,
    account_name=storage_account.name
)

# Upload the archive as a Blob
app_blob = storage.Blob(
    "app-blob",
    resource_group_name=resource_group.name,
    account_name=storage_account.name,
    container_name=blob_container.name,
    source=app_archive
)

# Create an App Service Plan
app_service_plan = web.AppServicePlan(
    "example-app-service-plan",
    resource_group_name=resource_group.name,
    sku=web.SkuDescriptionArgs(
        name="S1",
        tier="Standard",
        capacity=1
    ),
    location="EastUS",
    kind="app"
)

# Deploy the Web App, referencing the uploaded archive
web_app = web.WebApp(
    "example-web-app",
    resource_group_name=resource_group.name,
    server_farm_id=app_service_plan.id,
    location="EastUS",
    site_config=web.SiteConfigArgs(
        app_settings=[
            web.NameValuePairArgs(
                name="WEBSITE_RUN_FROM_PACKAGE",
                value= app_blob.url,
            )
        ],
    )
)

# Export the primary key of the Storage Account
primary_key = (
    pulumi.Output.all(resource_group.name, storage_account.name)
    .apply(
        lambda args: storage.list_storage_account_keys(
            resource_group_name=args[0], account_name=args[1]
        )
    )
    .apply(lambda accountKeys: accountKeys.keys[0].value)
)

pulumi.export("primary_storage_key", primary_key)
pulumi.export("app_url", web_app.default_host_name)

