---
name: clashctl-proxy
description: > 
  Manage mihomo/Clash Meta proxy via nelvko/clash-for-linux-install (clashctl).
  All CLI commands, Web API (delay test + switch nodes), Mixin config, Tun mode,
  subscription management, proxy env setup, and auto-switch script for finding
  the lowest-latency node. Designed for servers where GitHub:443 is blocked.
---

# clashctl-proxy

## Goal

Provide an organized proxy management capability for Linux servers using
[mihomo](https://github.com/MetaCubeX/mihomo) (Clash Meta kernel) managed
by [nelvko/clash-for-linux-install](https://github.com/nelvko/clash-for-linux-install)
(⭐12.5k). Used when GitHub:443 is blocked and HTTP_PROXY is needed.
Includes an automated script to test node latency and switch to the fastest node.

## Prerequisites

- mihomo installed at `/root/clashctl/` (standard installation path)
- systemd service `mihomo.service` running
- Web API key (`secret`) configured in mixin.yaml

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

## Using the Proxy

### For Hermes agents / shell

When GitHub:443 is unreachable (HTTPS blocked), set HTTP_PROXY:

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,100.64.0.0/10
```

Or use `clashproxy on` which sets these automatically.

### For cargo builds

```bash
source "$HOME/.cargo/env"
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
cargo build --release
```

### For git clone

SSH (port 22) works when HTTPS (443) is blocked:
```bash
git clone git@github.com:user/repo.git
```

## Web API (RESTful Control)

mihomo exposes an HTTP API at the `external-controller` address (default `0.0.0.0:9090`).

### Common API endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/proxies` | GET | List all proxies and groups |
| `/proxies/{name}` | GET | Get proxy/group detail |
| `/proxies/{name}` | PUT | Select node in a Selector group |
| `/proxies/{name}/delay` | GET | Test delay (params: timeout, url) |
| `/version` | GET | mihomo version |
| `/upgrade` | POST | Upgrade kernel |

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

## Auto-Switch: Fastest Node Detection

When the current proxy node is slow, run the auto-switch script to find the
fastest alternative node.

### Usage

```bash
python3 ~/.hermes/scripts/switch_proxy.py
```

The script:
1. Lists all nodes in the Selector group (default: "低调机场")
2. Tests each node's delay via mihomo API (5s timeout, tested against google.com)
3. Sorts by latency ascending
4. Switches to the fastest node if it's better than the current one
5. Prints results

### Example output

```
📡 当前节点: US 01｜电信优化
🔍 正在测试 33 个节点的延迟...
  JP 01｜高速专线: 113ms
  JP 05｜高速专线: 95ms
  HK 01｜移动专线: 338ms
  US 01｜电信优化: 200ms
  ...
⚡ 切换到 JP 05｜高速专线 (95ms)
✅ 已切换至 JP 05｜高速专线
```

### When to use

- GitHub HTTPS downloads (port 443) timeout or are slow
- `curl -s --max-time 10 https://github.com` returns non-200
- General network slowness from China to overseas resources
- Cargo builds / `npm install` are taking unusually long

### Script configuration

The script is at `switch_proxy.py` in this skill's scripts directory,
or installed at `~/.hermes/scripts/switch_proxy.py`.

Configuration constants (edit directly in the script):

| Constant | Default | Description |
|----------|---------|-------------|
| `API_BASE` | `http://127.0.0.1:9090` | mihomo API address |
| `SECRET` | `<YOUR_SECRET>` | API secret from mixin.yaml — **替换为此处示例值** |
| `GROUP_NAME` | `低调机场` | Selector group to manage |
| `TIMEOUT_MS` | `5000` | Per-node test timeout |
| `TEST_URL` | `https://www.google.com` | URL for latency test |

## Mixin Configuration

Mixin file (`/root/clashctl/resources/mixin.yaml`) overlays raw subscription config.
It supports prefix/suffix/override/inject patterns:

```yaml
rules:
  prefix:
    - DOMAIN-SUFFIX,google.com,低调机场
  suffix:
    - MATCH,DIRECT
proxies:
  override:
    - name: "JP 01｜高速专线"
      port: 443
proxy-groups:
  inject:
    低调机场:
      - "MyCustomNode"
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
- **Hysteria2 IPv6 nodes** → May timeout on servers without IPv6; the auto-switch script handles this gracefully (timeout = skipped)
- **Config edits** → Always edit `mixin.yaml`, never edit `runtime.yaml` directly (it gets regenerated on merge)
- **API secret mismatch** → Auto-switch script errors if SECRET doesn't match mixin.yaml's `secret` field
- **mihomo not running** → Script exits with API connection error; run `clashon` first
- **Only Selector groups can be switched** → URLTest/Fallback groups auto-manage their own nodes

## Verification

```bash
# Check service is running
systemctl status mihomo.service --no-pager

# Check proxy works
curl -x http://127.0.0.1:7890 -s --max-time 10 https://www.google.com -o /dev/null -w "%{http_code}"

# Check API is responding
curl -s --noproxy "*" -H "Authorization: Bearer $SECRET" http://127.0.0.1:9090/version

# Auto-switch test (~30-60s)
python3 ~/.hermes/scripts/switch_proxy.py
```
