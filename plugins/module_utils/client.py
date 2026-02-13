#!/usr/bin/python
# -*- coding: utf-8 -*-
import ssl
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from xml.etree import ElementTree as ET


class ISPManagerError(Exception):
    pass


class ISPManagerClient:
    """HTTP client for ISPmanager 5/6 API."""

    def __init__(self, api_url, username, password):
        self.api_url = api_url.rstrip("/")
        self.authinfo = f"{username}:{password}"
        self._ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self._ssl_ctx.check_hostname = False
        self._ssl_ctx.verify_mode = ssl.CERT_NONE
        self._ssl_ctx.set_ciphers('DEFAULT:@SECLEVEL=0')

    def _request(self, params):
        """Make HTTP GET request to ISPmanager API."""
        params["authinfo"] = self.authinfo
        params["out"] = "xml"
        url = f"{self.api_url}/ispmgr?{urlencode(params)}"

        try:
            resp = urlopen(url, context=self._ssl_ctx, timeout=30)
            body = resp.read()
        except (URLError, HTTPError) as e:
            raise ISPManagerError(f"API request failed: {e}")

        root = ET.fromstring(body)

        error = root.find("error")
        if error is not None:
            code = error.get("code", "")
            if not code:
                code_el = error.find("code")
                if code_el is not None:
                    code = code_el.text or ""
            msg_el = error.find("msg")
            msg = msg_el.text if msg_el is not None and msg_el.text else error.get("type", "Unknown error")
            raise ISPManagerError(f"ISPmanager error {code}: {msg}")

        return root

    def get_records(self, domain):
        """Get DNS records for a domain zone."""
        root = self._request({"func": "domain.sublist", "elid": domain})
        records = []
        for elem in root.findall(".//elem"):
            record = {child.tag: child.text or "" for child in elem}
            records.append(record)
        return records

    def create_record(self, domain, name, rtype, value, ttl):
        """Create a new DNS record."""
        return self._request({
            "func": "domain.sublist.edit",
            "sok": "yes",
            "plid": domain,
            "name": name,
            "sdtype": rtype,
            "addr": value,
            "ttl": str(ttl),
        })

    def update_record(self, domain, elid, name, rtype, value, ttl):
        """Update an existing DNS record."""
        return self._request({
            "func": "domain.sublist.edit",
            "sok": "yes",
            "plid": domain,
            "elid": elid,
            "name": name,
            "sdtype": rtype,
            "addr": value,
            "ttl": str(ttl),
        })

    def delete_record(self, domain, elid):
        """Delete a DNS record."""
        return self._request({
            "func": "domain.sublist.delete",
            "plid": domain,
            "elid": elid,
        })
