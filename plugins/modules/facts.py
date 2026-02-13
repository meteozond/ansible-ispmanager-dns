#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ispmanager.dns.plugins.module_utils.client import (
    ISPManagerClient,
    ISPManagerError,
)

DOCUMENTATION = """
---
module: ispmanager_dns_facts
short_description: Gather DNS records from ISPmanager
options:
  api_url:
    description: ISPmanager API URL
    required: True
  username:
    description: ISPmanager login
    required: True
  password:
    description: ISPmanager password
    required: True
  domains:
    description: List of domains to fetch records for
    required: True
    type: list
"""


def main():
    module = AnsibleModule(
        argument_spec={
            "api_url": {"required": True, "type": "str"},
            "username": {"required": True, "type": "str"},
            "password": {"required": True, "type": "str", "no_log": True},
            "domains": {"required": True, "type": "list"},
        },
        supports_check_mode=True,
    )

    client = ISPManagerClient(
        module.params["api_url"],
        module.params["username"],
        module.params["password"],
    )

    result = {}
    for domain in module.params["domains"]:
        try:
            records = client.get_records(domain)
            result[domain] = records
        except ISPManagerError as e:
            module.fail_json(
                msg="Failed to get records for {0}: {1}".format(
                    domain, str(e)
                )
            )

    module.exit_json(
        changed=False,
        ansible_facts={"ispmanager_dns": result},
    )


if __name__ == "__main__":
    main()
