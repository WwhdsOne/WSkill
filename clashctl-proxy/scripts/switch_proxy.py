#!/usr/bin/env python3
"""自动测速并切换到延迟最低的代理节点"""
import json, urllib.request, urllib.parse, sys, time

API_BASE = "http://127.0.0.1:9090"
SECRET = "YOUR_SECRET"  # 从 mixin.yaml 获取
GROUP_NAME = "低调机场"  # Selector 组名
TIMEOUT_MS = 5000
TEST_URL = "https://www.google.com"

def api_get(path):
    req = urllib.request.Request(f"{API_BASE}{path}")
    req.add_header("Authorization", f"Bearer {SECRET}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def test_delay(node_name):
    quoted = urllib.parse.quote(node_name, safe='')
    params = urllib.parse.urlencode({"timeout": TIMEOUT_MS, "url": TEST_URL})
    req = urllib.request.Request(f"{API_BASE}/proxies/{quoted}/delay?{params}")
    req.add_header("Authorization", f"Bearer {SECRET}")
    try:
        with urllib.request.urlopen(req, timeout=(TIMEOUT_MS // 1000) + 2) as resp:
            data = json.loads(resp.read())
            return data.get("delay")
    except:
        return None

def switch_node(group_name, node_name):
    quoted_group = urllib.parse.quote(group_name, safe='')
    data = json.dumps({"name": node_name}).encode()
    req = urllib.request.Request(
        f"{API_BASE}/proxies/{quoted_group}",
        data=data,
        method="PUT",
        headers={
            "Authorization": f"Bearer {SECRET}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 204
    except:
        return False

def main():
    # 获取组内所有节点
    proxies = api_get("/proxies")
    if "error" in proxies:
        print(f"❌ API连接失败: {proxies['error']}")
        return 1

    group_name = GROUP_NAME
    group = proxies.get("proxies", {}).get(group_name, {})
    if not group:
        for name, g in proxies.get("proxies", {}).items():
            if g.get("type") == "Selector":
                group = g
                group_name = name
                break

    all_nodes = group.get("all", [])
    current = group.get("now", "")
    nodes_to_test = [n for n in all_nodes if n not in ("DIRECT", "REJECT", "自动选择")]

    if not nodes_to_test:
        print("❌ 没有可测试的节点")
        return 1

    print(f"📡 当前节点: {current}")
    print(f"🔍 正在测试 {len(nodes_to_test)} 个节点的延迟...")

    results = []
    for node in nodes_to_test:
        delay = test_delay(node)
        status = f"{delay}ms" if delay else "❌超时"
        print(f"  {node}: {status}")
        if delay:
            results.append((delay, node))
        time.sleep(0.1)  # 避免打得太快

    if not results:
        print("❌ 所有节点均超时")
        return 1

    results.sort()
    best_delay, best_node = results[0]

    if best_node == current:
        print(f"✅ 当前节点 {best_node} ({best_delay}ms) 已是最优")
        return 0

    print(f"⚡ 切换到 {best_node} ({best_delay}ms)")
    if switch_node(group_name, best_node):
        print(f"✅ 已切换至 {best_node}")
        return 0
    else:
        print("❌ 切换失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
