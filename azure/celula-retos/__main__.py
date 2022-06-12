"""An Azure RM Python Pulumi program"""

from email.mime import application
import pulumi
import pulumi_azure_native as az
import base64

resourceGroupName = "celula-devopscloud"

vNetCidrs = ["10.11.0.0/16"]

subnetsCidrs = ["10.11.0.0/24", "10.110.1.0/24"]

securiryRules = [
    {
        "access": "Allow",
        "destination_address_prefix": "*",
        "destination_port_range": "80",
        "direction": "Inbound",
        "priority": 100,
        "protocol": "*",
        "source_address_prefix": "Internet",
        "source_port_range": "*",
    },
]

tags = {
    "Owner": "Andres Gomez",
    "Environment": pulumi.get_stack(),
    "ProjectName": pulumi.get_project(),
    "StackName": pulumi.get_stack(),
    "Team": "DA",
}

# Functions
def base64Encoder(message):
    message_bytes = message.encode("ascii")
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode("ascii")
    return base64_message


# irtual network
virtualNetwork = az.network.VirtualNetwork(
    "virtualNetwork" + pulumi.get_stack(),
    address_space=az.network.AddressSpaceArgs(
        address_prefixes=vNetCidrs,
    ),
    resource_group_name=resourceGroupName,
    tags=tags,
)

# Creating network security group
networkSecurityGroup = az.network.NetworkSecurityGroup(
    "networkSecurityGroup" + pulumi.get_stack(),
    resource_group_name=resourceGroupName,
    tags=tags,
)

# Creating custom security rules
networkSecurityRules = []

for i, securiryRule in enumerate(securiryRules):
    networkSecurityRules.append(
        az.network.SecurityRule(
            "networkSecurityRules" + pulumi.get_stack() + str(i),
            security_rule_name="rule" + pulumi.get_stack() + str(i),
            resource_group_name=resourceGroupName,
            network_security_group_name=networkSecurityGroup.name,
            access=securiryRule["access"],
            destination_address_prefix=securiryRule["destination_address_prefix"],
            destination_port_range=securiryRule["destination_port_range"],
            direction=securiryRule["direction"],
            priority=securiryRule["priority"],
            protocol=securiryRule["protocol"],
            source_address_prefix=securiryRule["source_address_prefix"],
            source_port_range=securiryRule["source_port_range"],
            opts=pulumi.ResourceOptions(depends_on=[networkSecurityGroup]),
        )
    )

# Creating subnets
vNetSubnets = []

for i, subnetsCidr in enumerate(subnetsCidrs):
    vNetSubnets.append(
        az.network.Subnet(
            "subnet" + pulumi.get_stack() + str(i),
            address_prefix=subnetsCidr,
            resource_group_name=resourceGroupName,
            # subnet_name="subnet1",
            virtual_network_name=virtualNetwork.name,
            network_security_group=az.network.NetworkSecurityGroupArgs(
                id=networkSecurityGroup
            ),
            opts=pulumi.ResourceOptions(depends_on=[networkSecurityGroup]),
        )
    )

# Allocate a public IP
publicIp = az.network.PublicIPAddress(
    "publicIp",
    resource_group_name=resourceGroupName,
    public_ip_allocation_method=az.network.IpAllocationMethod.DYNAMIC,
    tags=tags,
)

networkInterface = az.network.NetworkInterface(
    "networkInterface",
    resource_group_name=resourceGroupName,
    enable_accelerated_networking=True,
    ip_configurations=[
        az.network.NetworkInterfaceIPConfigurationArgs(
            name="webserveripconfig",
            public_ip_address=az.network.PublicIPAddressArgs(
                id=publicIp.id,
            ),
            subnet=az.network.SubnetArgs(
                id=vNetSubnets[0].id,
            ),
        )
    ],
    tags=tags,
    opts=pulumi.ResourceOptions(depends_on=vNetSubnets + [publicIp]),
)

initScript = """#! /bin/bash
sudo apt-get update
sudo apt-get install -y apache2
sudo systemctl start apache2
sudo systemctl enable apache2
echo "<h1>Demo Bootstrapping Azure Virtual Machine</h1>" | sudo tee /var/www/html/index.html"""

serverVm = az.compute.VirtualMachine(
    "serverVm",
    resource_group_name=resourceGroupName,
    tags=tags,
    hardware_profile=az.compute.HardwareProfileArgs(vm_size="Standard_DS1_v2"),
    network_profile=az.compute.NetworkProfileArgs(
        network_interfaces=[
            az.compute.NetworkInterfaceReferenceArgs(
                id=networkInterface.id,
                primary=True,
            )
        ],
    ),
    os_profile=az.compute.OSProfileArgs(
        admin_username="andresgo",
        admin_password="Andresgo01",
        computer_name="hostname",
        custom_data=base64Encoder(initScript),
        linux_configuration=az.compute.LinuxConfigurationArgs(
            patch_settings=az.compute.LinuxPatchSettingsArgs(
                assessment_mode="ImageDefault",
            ),
            provision_vm_agent=True,
            disable_password_authentication=False,
        ),
    ),
    storage_profile=az.compute.StorageProfileArgs(
        image_reference=az.compute.ImageReferenceArgs(
            offer="UbuntuServer",
            publisher="Canonical",
            sku="18.04-LTS",
            version="latest",
        ),
        os_disk=az.compute.OSDiskArgs(
            caching=az.compute.CachingTypes.READ_WRITE,
            create_option="FromImage",
            delete_option="Delete",
            managed_disk=az.compute.ManagedDiskParametersArgs(
                storage_account_type="Premium_LRS"
            ),
            name="myosdisk1",
        ),
    ),
    opts=pulumi.ResourceOptions(depends_on=[networkInterface]),
)
