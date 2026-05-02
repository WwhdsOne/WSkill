---
name: clashctl-proxy
description: > 
  Manage mihomo/Clash Meta proxy via nelvko/clash-for-linux-install (clashctl).
  Covers installation, all CLI commands, Web API (delay test + switch nodes),
  Mixin config, Tun mode, subscription management, and proxy env setup for
  Hermes agent. Designed for servers where GitHub:443 is blocked.
---

# clashctl-proxy

## Goal

Provide an organized proxy management capability for Linux servers using
[mihomo](https://github.com/MetaCubeX/mihomo) (Clash Meta kernel) managed
by [nelvko/clash-for-linux-install](https://github.com/nelvko/clash-for-linux-install)
(⭐12.5k). Used when GitHub:443 is blocked and HTTP_PROXY is needed.

## Prerequisites

- mihomo installed at `/root/clashctl/` (standard installation path)
- systemd service `mihomo.service` running
- Web API key (`secret`) configured

## File Layout

```
/root/clashctl/
├── bin/
│   ├── mihomo              # Clash Meta kernel
│   ├── yq                  # YAML processor
│   └── subconverter/       # Subscription converter
├── resources/
│   ├── config.yaml         # Raw subscription config
│   ├── mixin.yaml          # Custom overrides (highest priority)
│   ├── runtime.yaml        # Merged runtime config (config + mixin)
│   ├── profiles.yaml       # Subscription profile metadata
│   ├── profiles/           # Saved subscription files
│   ├── Country.mmdb        # GeoIP database
│   └── geosite.dat         # Geosite database
├── .env                    # Installation config (kernel, paths, version)
├── scripts/cmd/
│   └── clashctl.sh         # All CLI commands
├── install.sh
└── uninstall.sh
```

## CLI Commands

All commands available as both `clashctl <subcommand>` and direct aliases:

| Command | Alias | Function |
|---------|-------|----------|
| `clashctl on` | `clashon` | Start proxy kernel + set system proxy |
| `clashctl off` | `clashoff` | Stop kernel + unset system proxy |
| `clashctl status` | `clashstatus` | Check kernel status (via systemctl) |
| `clashctl log` | `clashlog` | View kernel logs (journalctl) |
| `clashctl proxy [on\|off]` | `clashproxy` | Toggle system proxy env vars only |
| `clashctl ui` | `clashui` | Print Web dashboard URLs |
| `clashctl secret [key]` | `clashsecret` | View/set Web API key |
| `clashctl sub add <url>` | `clashsub` | Add subscription |
| `clashctl sub ls` | `clashsub` | List subscriptions |
| `clashctl sub del <id>` | - | Delete subscription |
| `clashctl sub use <id>` | - | Switch to subscription |
| `clashctl sub update [id]` | - | Update subscription (--auto for cron, --convert for subconverter) |
| `clashctl sub log` | - | View subscription operation log |
| `clashctl mixin` | `clashmixin` | View Mixin config |
| `clashctl mixin -e` | - | Edit Mixin config (vim) |
| `clashctl mixin -c` | - | View raw subscription config |
| `clashctl mixin -r` | - | View runtime config |
| `clashctl tun [on\|off]` | `clashtun` | TUN mode (global transparent proxy, affects Docker too) |
| `clashctl upgrade [-v\|-r\|-a]` | `clashupgrade` | Upgrade kernel (release/alpha) |

## Using the Proxy in Hermes

When GitHub:443 is unreachable (HTTPS blocked), set HTTP_PROXY:

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,100.64.0.0/10
```

Or use `clashproxy on` which sets these automatically.

For `cargo` builds with proxy:
```bash
source "$HOME/.cargo/env"
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
cargo build --release
```

For `git clone` via SSH (port 22 works, 443 blocked):
```bash
git clone git@github.com:user/repo.git
```

## Web API (RESTful Control)

mihomo exposes an HTTP API at the `external-controller` address (default `0.0.0.0:9090`).

### Get all proxy groups and nodes

```bash
SECRET="your_secret"
curl -s --noproxy "*" -H "Authorization: Bearer $SECRET" \
  "http://127.0.0.1:9090/proxies"
```

### Test latency of a specific node

```bash
curl -s --noproxy "*" -H "Authorization: Bearer $SECRET" \
  "http://127.0.0.1:9090/proxies/$(python3 -c 'import urllib.parse; print(urllib.parse.quote("NODE_NAME"))')/delay" \
  --get --data-urlencode "timeout=5000" \
  --data-urlencode "url=https://www.google.com"
```

Response: `{"delay": 95}` or empty on timeout.

### Switch active node in a Selector group

```bash
curl -X PUT --noproxy "*" \
  -H "Authorization: Bearer $SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "NEW_NODE_NAME"}' \
  "http://127.0.0.1:9090/proxies/GROUP_NAME"
```

Returns `204 No Content` on success.

### Common API endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/proxies` | GET | List all proxies and groups |
| `/proxies/{name}` | GET | Get proxy/group detail |
| `/proxies/{name}` | PUT | Select node in a Selector group |
| `/proxies/{name}/delay` | GET | Test delay (params: timeout, url) |
| `/version` | GET | mihomo version |
| `/upgrade` | POST | Upgrade kernel (from mihomo itself) |

## Mixin Configuration

Mixin file (`/root/clashctl/resources/mixin.yaml`) overlays raw subscription config.
It supports prefix/suffix/override/inject patterns:

```yaml
# Mixin example
rules:
  prefix:
    - DOMAIN-SUFFIX,google.com,低调机场
  suffix:
    - MATCH,DIRECT
proxies:
  override:
    - name: "JP 01｜高速专线"
      port: 443    # override only specific fields
proxy-groups:
  inject:
    低调机场:
      - "MyCustomNode"   # inject into existing group
```

## Subscription Management

```bash
# Add a subscription
clashsub add "https://example.com/sub?token=xxx"

# List subscriptions (see IDs)
clashsub ls

# Switch to subscription by ID
clashsub use 1

# Update all subscriptions automatically (cron-based)
clashsub update --auto

# Update with subscription converter support
clashsub update --convert
```

## Pitfalls

- **GitHub:443 blocked** → Use SSH (`git@github.com:...`) for clones, or set HTTP_PROXY before using HTTPS
- **Node names with special characters** → Must URL-encode when using the REST API: `urllib.parse.quote(name)`
- **TUN mode + fake-ip** → `mixin.yaml` must include `proxy-server-nameserver` to prevent node domain resolution from returning fake-ip
- **Port conflicts** → `clashon` auto-detects and assigns random ports; check runtime.yaml if services fail to start
- **Hysteria2 IPv6 nodes** → May timeout on servers without IPv6; exclude from auto-testing
- **Config edits** → Always edit `mixin.yaml`, never edit `runtime.yaml` directly (it gets regenerated on merge)

## Verification

```bash
# Check service is running
systemctl status mihomo.service --no-pager

# Check proxy works
curl -x http://127.0.0.1:7890 -s --max-time 10 https://www.google.com -o /dev/null -w "%{http_code}"

# Check API is responding
curl -s --noproxy "*" -H "Authorization: Bearer $SECRET" http://127.0.0.1:9090/version

# Test all nodes latency
# See proxy-auto-switch skill for automated testing
```
