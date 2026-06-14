# AI Agent 介入远程服务器操作的脱敏安全流程

**标签**：#agent-skills #network #tools #deployment #credential #troubleshooting #experience
**来源**：实践总结（已脱敏）
**收录日期**：2026-06-14
**来源日期**：2026-06-13
**更新日期**：2026-06-14
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（本机实测 + 服务器只读验证）
**适用版本**：Codex Desktop + Agent Skills + OpenSSH + Linux/Nginx/BaoTa 类 Web 服务器

### 概要

让 AI Agent 介入远程服务器时，关键不是把账号密码直接塞进对话，而是建立“本地密钥文件 + 脱敏入口记录 + 操作前验证 + 最小权限命令 + 可撤销授权”的闭环。若需要跨会话复用，应把流程固化为本地 Skill，但 Skill 只能记录目标说明、占位符、密钥路径策略和验证命令，不能记录私钥正文。

### 内容

#### 场景

适用于这些需求：

- 用户希望 AI Agent 通过 SSH 检查或操作自己的远程服务器。
- 需要让后续新会话知道“默认服务器”是哪一类机器，但不暴露完整资产信息。
- 需要把服务器部署、Nginx/SSL、静态站点发布等操作变成可重复流程。
- 需要保留可撤销入口，避免长期凭据散落在聊天记录或文档里。

#### 核心原则

1. 只在本机文件系统保存私钥，聊天记录、Skill、知识库记录都不得包含私钥正文。
2. Skill 或知识库只记录脱敏入口：`<server-user>@<server-host>`、`<local-key-path>`、`<public-key-marker>`、`<site-root>`、`<vhost-config>` 等占位符。
3. 任何有状态操作前必须先做只读验证：密钥存在、权限合理、SSH 可达、远端用户符合预期、主机身份符合预期。
4. 服务器操作必须先查现状，再执行变更；不能凭历史记忆直接改配置。
5. 高风险动作必须保留撤销路径，例如能通过 `<public-key-marker>` 在 `authorized_keys` 中删除对应授权行。
6. Nginx/SSL/站点部署类操作必须在变更后做服务级验证，例如 `nginx -t`、HTTPS HEAD 请求、页面关键内容检查。

#### 推荐流程

##### 1. 建立一次性或可撤销 SSH 入口

本地生成专用密钥对，给公钥追加可识别注释：

```bash
ssh-keygen -t ed25519 -f <local-key-path> -C <public-key-marker>
chmod 600 <local-key-path>
```

把公钥加入服务器用户的 `authorized_keys`，并确保该行带有 `<public-key-marker>`。后续撤销时只删除这一行，不覆盖整个 `authorized_keys` 文件。

##### 2. 第一次连接必须只读验证

```bash
ssh -i <local-key-path> -o IdentitiesOnly=yes <server-user>@<server-host> \
  'printf "user=%s\nhost=%s\nkernel=%s\n" "$(whoami)" "$(hostname)" "$(uname -sr)"'
```

验证点：

- `whoami` 是否符合预期。
- `hostname` 是否符合当前服务器身份记录。
- 内核和系统信息是否与目标机器大体一致。
- `authorized_keys` 中是否能定位到 `<public-key-marker>`。

##### 3. 固化为本地 Skill

本地 Skill 应包含三类信息：

- 触发条件：用户说“操作我的服务器”、提到目标项目域名、宝塔、Nginx、部署、SSL 等时触发。
- 操作纪律：先验证身份、先读现状、变更前备份关键配置、变更后执行服务校验。
- 脚本入口：封装 SSH 参数，降低每次重写命令导致的失误。

Skill 不应包含：

- 私钥正文。
- 完整公网 IP、真实域名、个人用户名、本机绝对路径等可公开反推资产的信息。
- 长期 token、密码、面板口令、Cookie 或 API key。

##### 4. 远程操作前的最小检查

每次新会话接手时，至少执行：

```bash
bash <skill-dir>/scripts/server-ssh.sh check
bash <skill-dir>/scripts/server-ssh.sh status
```

`check` 只验证身份和授权标记；`status` 可检查磁盘、Nginx 配置、站点根目录等基础状态。若任务只是回答“当前是否可用”，不要执行写入型命令。

##### 5. 变更类操作的验证门禁

对 Nginx、SSL、站点根目录、部署产物做变更时：

1. 先读取目标配置或目录列表。
2. 对重要配置创建时间戳备份。
3. 只上传构建产物或明确目标文件，避免全量覆盖未知目录。
4. 运行服务配置检查：

```bash
<nginx-bin> -t
```

5. 配置检查通过后才 reload。
6. 用固定解析或服务端本地请求验证目标站点：

```bash
curl --resolve <project-domain>:443:<server-host> -I https://<project-domain>/
```

7. 记录验证结果、未覆盖范围和剩余风险。

#### 敏感信息脱敏规则

正式记录和 Skill 描述中应替换：

| 原始信息类型 | 记录写法 |
|---|---|
| 真实公网 IP / 主机名 | `<server-host>` |
| SSH 用户 | `<server-user>` |
| 本机私钥绝对路径 | `<local-key-path>` |
| 公钥注释 / 授权标记 | `<public-key-marker>` |
| 真实域名 | `<project-domain>` |
| 站点根目录 | `<site-root>` |
| Nginx 配置文件路径 | `<vhost-config>` |
| 证书、token、私钥正文 | 不记录 |

如果某个值会让读者直接定位到真实服务器或本机环境，应优先占位；如果必须保留用于本地自动化，应只放在私有 Skill 的本地引用里，不进入可共享知识库记录。

#### 失败模式

- 只记住“服务器能连”，不重新验证身份：可能操作错机器或旧授权已失效。
- 把私钥正文贴进聊天或 Skill：会扩大泄露面，且难以彻底撤回。
- 覆盖 `authorized_keys`：可能把用户自己的登录方式一起清掉。
- Nginx 配置改完直接 reload：配置错误会导致站点不可用。
- 靠 DNS 默认解析验证：本地 DNS 缓存或解析未生效时，可能误判站点状态。
- 把真实域名、IP、本机路径写入共享知识库：会把一次性运维上下文变成长期暴露面。

### 关键代码

一个最小 SSH helper 脚本结构如下，实际使用时把占位符放在本地私有 Skill 或本机环境变量中：

```bash
#!/usr/bin/env bash
set -euo pipefail

HOST="${SERVER_HOST:-<server-user>@<server-host>}"
KEY="${SERVER_KEY:-<local-key-path>}"
MARKER="${SERVER_KEY_MARKER:-<public-key-marker>}"

require_key() {
  test -f "$KEY" || { echo "missing key: $KEY" >&2; exit 2; }
}

ssh_base() {
  ssh -i "$KEY" \
    -o IdentitiesOnly=yes \
    -o StrictHostKeyChecking=accept-new \
    -o ConnectTimeout=10 \
    "$HOST" "$@"
}

case "${1:-}" in
  check)
    require_key
    ssh_base "whoami; hostname; uname -sr; grep -n '$MARKER' ~/.ssh/authorized_keys >/dev/null 2>&1 || true"
    ;;
  run)
    shift
    require_key
    ssh_base "$@"
    ;;
  *)
    echo "usage: server-ssh.sh check | run <command>" >&2
    exit 2
    ;;
esac
```

### 相关记录

- [宝塔 Nginx SSL 配置文件冲突处理](./bt-nginx-ssl-config-conflict.md) - 服务器站点 SSL/Nginx 配置变更时的相邻验证经验。
- [VitePress 宝塔 Nginx 部署 403/404 与 cleanUrls 刷新修复](./vitepress-nginx-deploy-403-cleanurls.md) - 静态站点部署与 Nginx 路由验证经验。
- [Git HTTPS 拉取失败，改用 SSH 协议解决](./git-https-fail-switch-ssh.md) - SSH 作为稳定操作入口的相邻经验。
- [Agent Skills 规范](./agent-skills-spec.md) - 将操作流程固化为 Skill 的格式背景。
- [Claude Code Skill 触发模式与 Hook 提升自动触发率](./claude-code-skill-hook-trigger-boost.md) - Skill 触发机制和触发可靠性相关经验。

### 验证记录

- [2026-06-14] 初次记录，来源为一次远程服务器介入与本地 Skill 固化实践；已完成脱敏审查，移除真实公网地址、真实域名、本机绝对路径、SSH 私钥路径、授权标记、高权限 SSH 用户、站点目录和具体 Nginx 配置路径，仅保留占位符与可复用安全流程。
- [2026-06-14] 只读验证链路已在原环境实测：本地 Skill 结构校验通过，SSH helper 脚本语法通过，安装后的 helper 可返回远端用户、主机名、内核信息与授权标记匹配结果。正式记录不保留这些原始值。

---
