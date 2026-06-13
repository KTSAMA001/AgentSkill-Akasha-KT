# 宝塔 Nginx SSL 配置文件冲突处理

**标签**：#tools #network #experience #deployment #proxy #troubleshooting
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-07
**来源日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：宝塔面板 9.x + Nginx 1.26

### 概要

宝塔 HTML 类型站点可能使用 `html_{域名}.conf`，而 SSL 模块按 `{域名}.conf` 查找配置，导致“找不到标识信息”或重复 server 配置冲突。可先手动配置 SSL，再让面板保存同步状态，并排查重复配置文件。

### 内容

#### 问题

宝塔面板 SSL 部署时报“找不到标识信息”：

```text
站点配置文件中未找到标识信息【#error_page 404/404.html;】
```

#### 根因

宝塔创建 HTML 类型站点时，Nginx 配置文件命名为 `html_{域名}.conf`。但宝塔 SSL 模块按 `{域名}.conf` 查找配置文件。

| 模块 | 查找的文件名 | 实际文件 |
|------|--------------|----------|
| 站点管理（配置文件编辑） | `html_{域名}.conf` | 存在，标记完整 |
| SSL 部署模块 | `{域名}.conf` | 不存在或为空 |

两个模块的命名规范不一致，导致 SSL 模块在错误文件中找标记。

#### 解决方案

方案 A：手动 SSL

- 直接在配置文件中手写 `listen 443 ssl` 和 `ssl_certificate` 等指令。
- 可行，但面板状态可能不同步。

方案 B：同步面板状态

- 创建符号链接 `ln -s html_{域名}.conf {域名}.conf`。
- 或先手动配好 SSL，再去面板点“保存并启用证书”，让面板识别已有 SSL 配置并同步状态。

最终操作流程：

1. 手动在 `html_{域名}.conf` 中添加 443 server 块和 SSL 证书配置。
2. 80 端口 server 块改为 HTTPS 跳转。
3. 运行 `nginx -t && nginx -s reload` 确认生效。
4. 回到宝塔 SSL 面板点“保存并启用证书”，让面板同步状态。
5. 如果出现 `conflicting server name` 警告，检查并删除多余的重复配置文件。

注意：宝塔面板操作 SSL 时可能自动创建 `{域名}.conf`，导致两份同名 server 配置同时加载。发现 `nginx -t` 有 `conflicting server name` 警告时，需排查并合并或删除重复文件。

### 关键代码

```bash
nginx -t
nginx -s reload
```

### 相关记录

- [Akasha Webhook PM2 守护与 HTTPS 反向代理](./akasha-webhook-pm2-https-proxy.md) - SSL 启用后 webhook 迁移到 HTTPS 反向代理。
- [VitePress 宝塔 Nginx 部署 403/404 与 cleanUrls 刷新修复](./vitepress-nginx-deploy-403-cleanurls.md) - 同站点 Nginx root 和 `try_files` 配置。

### 验证记录

- [2026-02-07] 手动 SSL 配置和面板保存同步流程验证通过。
- [2026-02-07] 重复配置导致 `conflicting server name` 的排查路径已确认。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---
