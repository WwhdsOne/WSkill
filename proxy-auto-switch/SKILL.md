---
name: proxy-auto-switch
description: > 
  Auto-detect and switch to the lowest-latency mihomo/Clash Meta proxy node
  when network is slow or GitHub:443 is blocked. Uses mihomo Web API to test
  node delays and switch Selector group. Includes switch_proxy.py script.
---

# proxy-auto-switch

## Goal

Automatically find and switch to the fastest proxy node when the current node
is slow or unresponsive. Useful for servers behind the Great Firewall where
GitHub:443 is frequently blocked.

## Prerequisites

- mihomo/Clash Meta running with Web API enabled (default: `0.0.0.0:9090`)
- API secret configured in runtime config
- Python 3.6+
- `curl` available

## Files

- `scripts/switch_proxy.py` — The auto-switch script (also copied to `~/.hermes/scripts/switch_proxy.py`)

## Usage

### Run auto-switch (manual)

```bash
python3 ~/.hermes/scripts/switch_proxy.py
```

This will:
1. List all non-DIRECT/REJECT nodes in the Selector group (default: "低调机场")
2. Test each node's delay via mihomo API (5s timeout, tested against google.com)
3. Sort by latency ascending
4. If current node is not the fastest, switch to the best one
5. Print results

### When to use

- GitHub HTTPS downloads (port 443) timeout or are slow
- `curl -s --max-time 10 https://github.com` returns non-200
- General network slowness from China to overseas resources
- Cargo builds/`npm install` are taking unusually long

### Integration with Hermes

When Hermes detects network slowness (e.g., GitHub downloads fail), it can:

```bash
# Step 1: auto-switch to best node
python3 ~/.hermes/scripts/switch_proxy.py

# Step 2: retry the operation (now with faster proxy)
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

## How it works

The script uses the mihomo REST API:

1. `GET /proxies` — discovers the Selector group and all available nodes
2. `GET /proxies/{name}/delay?timeout=5000&url=https://google.com` — tests each node
3. `PUT /proxies/{group_name}` — switches to the lowest-latency node

## Script reference

```
switch_proxy.py

Environment variables (or edit directly):
  API_BASE    — mihomo API address (default: http://127.0.0.1:9090)
  SECRET      — API secret (default: wwh852456)
  GROUP_NAME  — Selector group name (default: 低调机场)
  TIMEOUT_MS  — Per-node test timeout (default: 5000)
  TEST_URL    — URL for latency test (default: https://www.google.com)
```

## Output examples

```
📡 当前节点: JP 05｜高速专线
🔍 正在测试 33 个节点的延迟...
  JP 01｜高速专线: 113ms
  JP 05｜高速专线: 95ms
  HK 01｜移动专线: 338ms
  ...
✅ 当前节点 JP 05｜高速专线 (95ms) 已是最优
```

```
📡 当前节点: US 01｜电信优化
🔍 正在测试 33 个节点的延迟...
  ...
⚡ 切换到 JP 05｜高速专线 (95ms)
✅ 已切换至 JP 05｜高速专线
```

## Pitfalls

- **Hysteria2 IPv6 nodes** will timeout on servers without IPv6 — that's expected
- **API secret mismatch** — script errors if SECRET doesn't match mixin.yaml's `secret` field
- **mihomo not running** — script exits with API connection error
- **Only Selector groups can be switched** — URLTest/Fallback groups auto-manage their own nodes
- **Delay test depends on Google being accessible** — if no proxy works at all, all nodes will timeout

## Verification

```bash
# Quick test (takes ~30-60s depending on node count)
python3 ~/.hermes/scripts/switch_proxy.py

# Direct API test without the script
SECRET="wwh852456"
curl -s --noproxy "*" -H "Authorization: Bearer $SECRET" \
  "http://127.0.0.1:9090/proxies/%E4%BD%8E%E8%B0%83%E6%9C%BA%E5%9C%BA/delay?timeout=5000&url=https://www.google.com"
```
