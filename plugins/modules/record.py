#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ispmanager.dns.plugins.module_utils.client import (
    ISPManagerClient,
    ISPManagerError,
)

DOCUMENTATION = """
---
module: ispmanager_dns
short_description: Manage DNS records via ISPmanager API
options:
  api_url:
    description: ISPmanager API URL (e.g. https://host:1500)
    required: true
  username:
    description: ISPmanager login
    required: true
  password:
    description: ISPmanager password
    required: true
  domain:
    description: DNS zone (e.g. erix.ru)
    required: true
  name:
    description: Record name (subdomain, e.g. nomie)
    required: true
  type:
    description: DNS record type
    default: A
    choices: [A, AAAA, CNAME, MX, NS, TXT]
  value:
    description: Record value (string or list for MX/NS)
    type: raw
  ttl:
    description: TTL in seconds
    default: 3600
  state:
    description: Desired state
    default: present
    choices: [present, absent]
author: Ansible
"""

EXAMPLES = """
- name: Create A record
  ispmanager_dns:
    api_url: "https://delta.netbreeze.net:1500"
    username: admin
    password: secret
    domain: erix.ru
    name: nomie
    value: "1.2.3.4"

- name: Create multiple NS records
  ispmanager_dns:
    api_url: "https://delta.netbreeze.net:1500"
    username: admin
    password: secret
    domain: erix.ru
    name: cdn
    type: NS
    value:
      - ns1.zerocdn.com.
      - ns2.zerocdn.com.

- name: Remove record
  ispmanager_dns:
    api_url: "https://delta.netbreeze.net:1500"
    username: admin
    password: secret
    domain: erix.ru
    name: old-host
    type: A
    value: "1.2.3.4"
    state: absent
"""

# ISPmanager field name variants
_TYPE_KEYS = ("rtype", "type", "dtype")
_VALUE_KEYS = ("addr", "value")
_ID_KEYS = ("key", "id")


def _normalize_values(value):
    """Normalize value to list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _get_field(record, keys, default=""):
    """Get first matching field from record."""
    for k in keys:
        if k in record:
            return record[k]
    return default


def _find_records(records, name, rtype, domain=None):
    """Find records matching name and type."""
    result = []
    apex_names = {"@", ""}
    if domain:
        apex_names.add(domain)
        apex_names.add(domain + ".")

    for rec in records:
        rec_name = rec.get("name", "")
        if name == "@":
            if rec_name not in apex_names:
                continue
        elif rec_name != name:
            continue

        rec_type = _get_field(rec, _TYPE_KEYS)
        if rec_type.upper() == rtype.upper():
            result.append(rec)
    return result


def _make_result(is_error, changed, meta, cache=None):
    """Create standardized result tuple."""
    return (is_error, changed, meta, cache)


def ispmanager_dns_present(client, params, check_mode=False):
    """Ensure DNS records are present."""
    domain = params["domain"]
    name = params["name"]
    rtype = params["type"]
    desired = set(_normalize_values(params["value"]))
    ttl = params["ttl"]
    cache = params.get("_cache")

    if cache is not None:
        records = list(cache)
    else:
        try:
            records = client.get_records(domain)
        except ISPManagerError as e:
            return _make_result(True, False, {"error": str(e)})

    existing = _find_records(records, name, rtype, domain)
    existing_map = {_get_field(r, _VALUE_KEYS): r for r in existing}
    existing_vals = set(existing_map.keys())

    to_create = desired - existing_vals
    to_delete = existing_vals - desired

    meta = {"created": [], "deleted": []}
    changed = False

    # Delete extra records
    for val in to_delete:
        elid = _get_field(existing_map[val], _ID_KEYS, None)
        if elid is None:
            return _make_result(
                True, changed,
                {"error": f"No record ID for delete: {val}"},
                records
            )
        if not check_mode:
            try:
                client.delete_record(domain, elid)
            except ISPManagerError as e:
                return _make_result(True, changed, {"error": str(e)}, records)
        changed = True
        meta["deleted"].append(val)

    # Create missing records
    for val in to_create:
        if not check_mode:
            try:
                client.create_record(domain, name, rtype, val, ttl)
            except ISPManagerError as e:
                return _make_result(True, changed, {"error": str(e)}, records)
        changed = True
        meta["created"].append(val)

    n = len(meta["created"]) + len(meta["deleted"])
    if n == 0:
        meta["msg"] = "already up to date"
    else:
        verb = "to change" if check_mode else "changed"
        meta["msg"] = f"{n} record{'s' if n != 1 else ''} {verb}"

    return _make_result(False, changed, meta, records)


def ispmanager_dns_absent(client, params, check_mode=False):
    """Ensure DNS records are absent."""
    domain = params["domain"]
    name = params["name"]
    rtype = params["type"]
    values = _normalize_values(params.get("value"))
    cache = params.get("_cache")

    if cache is not None:
        records = list(cache)
    else:
        try:
            records = client.get_records(domain)
        except ISPManagerError as e:
            return _make_result(True, False, {"error": str(e)})

    existing = _find_records(records, name, rtype, domain)
    if not existing:
        return _make_result(False, False, {"msg": "already absent"}, records)

    if values:
        target_vals = set(values)
        to_delete = [r for r in existing
                     if _get_field(r, _VALUE_KEYS) in target_vals]
    else:
        to_delete = existing

    if not to_delete:
        return _make_result(False, False, {"msg": "already absent"}, records)

    meta = {"deleted": []}
    changed = False

    for rec in to_delete:
        elid = _get_field(rec, _ID_KEYS, None)
        if elid is None:
            return _make_result(
                True, changed,
                {"error": "No record ID for delete"},
                records
            )
        if not check_mode:
            try:
                client.delete_record(domain, elid)
            except ISPManagerError as e:
                return _make_result(True, changed, {"error": str(e)}, records)
        changed = True
        meta["deleted"].append(_get_field(rec, _VALUE_KEYS))

    n = len(meta["deleted"])
    verb = "to delete" if check_mode else "deleted"
    meta["msg"] = f"{n} record{'s' if n != 1 else ''} {verb}"

    return _make_result(False, changed, meta, records)


def main():
    module = AnsibleModule(
        argument_spec={
            "api_url": {"required": True, "type": "str"},
            "username": {"required": True, "type": "str"},
            "password": {"required": True, "type": "str", "no_log": True},
            "domain": {"required": True, "type": "str"},
            "name": {"required": True, "type": "str"},
            "type": {
                "default": "A",
                "choices": ["A", "AAAA", "CNAME", "MX", "NS", "TXT"],
                "type": "str",
            },
            "value": {"type": "raw"},
            "ttl": {"default": 3600, "type": "int"},
            "state": {
                "default": "present",
                "choices": ["present", "absent"],
                "type": "str",
            },
            "_cache": {"type": "list", "default": None},
        },
        required_if=[("state", "present", ["value"])],
        supports_check_mode=True,
    )

    client = ISPManagerClient(
        module.params["api_url"],
        module.params["username"],
        module.params["password"],
    )

    handlers = {
        "present": ispmanager_dns_present,
        "absent": ispmanager_dns_absent,
    }

    is_error, changed, result, cache = handlers[module.params["state"]](
        client, module.params, module.check_mode
    )

    if is_error:
        module.fail_json(msg=result.get("error", "Unknown error"), **result)
    module.exit_json(changed=changed, **result)


if __name__ == "__main__":
    main()
