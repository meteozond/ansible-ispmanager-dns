# Ansible Collection: ispmanager.dns

Manage DNS records via ISPmanager API.

## Module usage

```yaml
# Create/update single record
- ispmanager.dns.record:
    api_url: "https://panel.example.com:1500"
    username: admin
    password: secret
    domain: example.com
    name: www
    type: A
    value: "1.2.3.4"

# Multiple values for same name (MX, NS)
- ispmanager.dns.record:
    api_url: "https://panel.example.com:1500"
    username: admin
    password: secret
    domain: example.com
    name: "@"
    type: MX
    value:
      - "ASPMX.L.GOOGLE.COM."
      - "ALT1.ASPMX.L.GOOGLE.COM."
      - "ALT2.ASPMX.L.GOOGLE.COM."

# Delete record
- ispmanager.dns.record:
    api_url: "https://panel.example.com:1500"
    username: admin
    password: secret
    domain: example.com
    name: old
    type: A
    value: "1.2.3.4"
    state: absent

# Gather facts
- ispmanager.dns.facts:
    api_url: "https://panel.example.com:1500"
    username: admin
    password: secret
    domains:
      - example.com
      - example.org
```

## Role usage

Role accepts `domains` dict and manages each record individually:

```yaml
- hosts: localhost
  roles:
    - role: ispmanager.dns.manage
      vars:
        isp_url: "https://panel.example.com:1500"
        isp_user: admin
        isp_pass: secret
        domains:
          example.com:
            a:
              www: "1.2.3.4"
            cname:
              mail: "ghs.googlehosted.com."
            mx:
              "@":
                - "ASPMX.L.GOOGLE.COM."
                - "ALT1.ASPMX.L.GOOGLE.COM."
        deleted_domains:
          example.com:
            cname:
              old: "old.example.com."
```

## Installation

### From Ansible Galaxy

```bash
ansible-galaxy collection install ispmanager.dns
```

### From Git repository

```bash
ansible-galaxy collection install git+https://github.com/YOUR_USERNAME/ansible-ispmanager-dns.git
```

### Using requirements.yml

```yaml
# requirements.yml
collections:
  - name: ispmanager.dns
    source: https://github.com/YOUR_USERNAME/ansible-ispmanager-dns.git
    type: git
```

Then install:

```bash
ansible-galaxy collection install -r requirements.yml
```

### Local installation (for development)

```bash
ansible-galaxy collection install /path/to/ansible-ispmanager-dns
```

## Modules

- `ispmanager.dns.record` — create/delete DNS records
- `ispmanager.dns.facts` — gather current DNS records

## Role

- `ispmanager.dns.manage` — full DNS management with diff


## Links

- [ISPmanager](https://www.ispmanager.com/)
- [ISPmanager API Documentation](https://docs.ispmanager.com/ispmanager6/developer-api)


## Requirements

- Python 3.8+
- [ISPmanager](https://www.ispmanager.com/) 5 or 6
- No external dependencies (uses only stdlib)


## License

MIT
