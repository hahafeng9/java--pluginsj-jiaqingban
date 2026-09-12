#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键补丁:节点/探针 UUID 拆分 + 默认静默日志(自动修改 App.java)"""
import pathlib
import re

APP = pathlib.Path("src/main/java/com/example/sbx/App.java")
s = APP.read_text(encoding="utf-8")


def rep(old, new):
    global s
    if old not in s:
        print(f"[WARN] 未找到: {old[:60]}")
        return
    s = s.replace(old, new)
    print(f"[OK] 替换: {old[:50]}...")


# 1) 拆成 NODE_UUID + PROBE_UUID
rep(
    'private static final String UUID = env("UUID", "dbb4b08c-011a-44df-9012-d61bd72ea28c");',
    'private static final String NODE_UUID = env("UUID", "dbb4b08c-011a-44df-9012-d61bd72ea28c");\n'
    '    private static final String PROBE_UUID = env("PROBE_UUID", "");'
)

# 2) sing-box 各种 inbound 全部改用 NODE_UUID
rep('listOf(mapOf("uuid", UUID)),', 'listOf(mapOf("uuid", NODE_UUID)),')  # vmess
rep('listOf(mapOf("uuid", UUID, "flow", "xtls-rprx-vision")),',
    'listOf(mapOf("uuid", NODE_UUID, "flow", "xtls-rprx-vision")),')      # vless
rep('listOf(mapOf("password", UUID)),', 'listOf(mapOf("password", NODE_UUID)),')  # hysteria2 + anytls
rep('listOf(mapOf("uuid", UUID, "password", UUID)),',
    'listOf(mapOf("uuid", NODE_UUID, "password", NODE_UUID)),')            # tuic
rep('listOf(mapOf("username", UUID.substring(0, 8), "password", UUID.substring(UUID.length() - 12)))',
    'listOf(mapOf("username", NODE_UUID.substring(0, 8), "password", NODE_UUID.substring(NODE_UUID.length() - 12)))')  # s5

# 3) 哪吒探针 config.yaml 用 PROBE_UUID(留空则回退 NODE_UUID)
rep('"uuid: " + UUID;', '"uuid: " + (PROBE_UUID.isEmpty() ? NODE_UUID : PROBE_UUID);')

# 4) generateLinks 分享链接全部改用 NODE_UUID
rep('"id", UUID, "aid", "0",', '"id", NODE_UUID, "aid", "0",')
rep('"tuic://" + UUID + ":" + UUID + "@"', '"tuic://" + NODE_UUID + ":" + NODE_UUID + "@"')
rep('"hysteria2://" + UUID + "@"', '"hysteria2://" + NODE_UUID + "@"')
rep('"vless://" + UUID + "@"', '"vless://" + NODE_UUID + "@"')
rep('"anytls://" + UUID + "@"', '"anytls://" + NODE_UUID + "@"')
rep('UUID.substring(0, 8) + ":" + UUID.substring(UUID.length() - 12)',
    'NODE_UUID.substring(0, 8) + ":" + NODE_UUID.substring(NODE_UUID.length() - 12)')

# 5) 默认静默(不输出日志)
rep('env("SHOW_LOG", "true")', 'env("SHOW_LOG", "false")')

# 检查还有没有残留的旧 UUID 标识符(排除 env("UUID") 字符串本身)
leftover = [m for m in re.findall(r'\bUUID\b', s) if m != '"UUID"']
if leftover:
    print(f"[WARN] 还有 {len(leftover)} 处残留 UUID 标识符,请检查!")
else:
    print("[OK] 已无残留 UUID 标识符,NODE_UUID/PROBE_UUID 全部就位。")

APP.write_text(s, encoding="utf-8")
print("完成:App.java 已自动修改。")
