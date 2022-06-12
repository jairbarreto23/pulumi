import base64

securiryRules = [
    {
        "access": "Allow",
        "destination_address_prefix": "*",
        "destination_port_range": "80",
        "direction": "Inbound",
        "priority": 100,
        "protocol": "*",
        "source_address_prefix": "*",
        "source_port_range": "*",
    },
]

for i, securiryRule in enumerate(securiryRules):
    print(i, securiryRule["access"])

initScript = """#!/bin/bash\n
echo "Hello, World!" > index.html
nohup python -m SimpleHTTPServer 80 &"""

print(initScript)


def base64Encoder(message):
    message_bytes = message.encode("ascii")
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode("ascii")
    return base64_message


initScriptBase64 = base64Encoder(initScript)
print(initScriptBase64)

list1 = ["item0", "item1", "item2"]
list2 = ["item3", "item4"]

listjoined = list1 + list2

print(listjoined)
