# Akasha Webhook PM2 守护与 HTTPS 反向代理

**标签**：#web #network #experience #cicd #deployment #github-actions #proxy #troubleshooting
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-07
**来源日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：Node.js webhook + pm2 + Nginx 1.26 + GitHub Webhook

### 概要

Akasha Web webhook 服务可用 pm2 守护在本机端口监听 GitHub push，再由 Nginx 在 HTTPS `/webhook` 路径反向代理到本机服务。启用 SSL 后应关闭公网直连非标端口，并让 GitHub Webhook 使用 HTTPS 标准端口。

### 内容

#### webhook 自动构建

webhook 服务使用 express 监听 3721 端口，接收 GitHub push 事件后自动执行 sync + build。

要点：

- 使用 `pm2 start server/webhook.mjs --name akasha-webhook` 守护运行。
- `pm2 save && pm2 startup` 实现开机自启。
- webhook 脚本中使用 `./node_modules/.bin/vitepress build`，避免 `npx` 缓存陷阱。
- GitHub 两个仓库都需要配置 webhook。

#### webhook 自更新的“鸡蛋问题”

`webhook.mjs` 接收 push event 后执行 sync + build，但脚本自身的更新也需要 git pull。如果 `webhook.mjs` 代码有变更，旧版本不会自动拉取新代码。

方案是在 `webhook.mjs` 的 `runBuild()` 开头增加自更新步骤：

```javascript
// Step 0: 更新 Web 仓库自身代码
execSync('git checkout . && git clean -fd', { cwd: PROJECT_ROOT })
execSync('git pull --ff-only', { cwd: PROJECT_ROOT, timeout: 60000 })
```

首次部署这个修改时，服务器上运行的是旧版 webhook，因此必须手动执行一次：

```bash
git pull
pm2 restart akasha-webhook
```

之后 webhook 才能自举更新。

#### 从 HTTP 直连迁移到 HTTPS 反向代理

启用 SSL 后，GitHub Webhook 不应继续使用明文 HTTP + 非标端口直连。应通过 Nginx 反向代理，让 GitHub 走 HTTPS 标准端口访问。

架构变更：

```text
之前：GitHub -> HTTP:3721 -> Node.js（直连，需开放 3721 端口）
之后：GitHub -> HTTPS:443 -> Nginx 解密 -> HTTP -> 127.0.0.1:3721 -> Node.js
```

Nginx 配置应添加在 443 server 块内：

```nginx
location /webhook {
    proxy_pass http://127.0.0.1:3721;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
}
```

关键点：

- Node.js 程序无需改动，继续监听 `127.0.0.1:3721`。
- `proxy_pass` 路径不带尾部 `/`，保持请求路径原样转发。
- `proxy_read_timeout 300s` 避免构建时间长导致 Nginx 超时断开。
- 3721 端口可以关闭外网访问，只允许本机访问。
- GitHub Webhook URL 改为 HTTPS，并启用 SSL verification。

### 关键代码

见“内容”中的 pm2 命令、自更新步骤和 Nginx `/webhook` 反向代理配置。

### 相关记录

- [Akasha Web 同步脚本与 Git 部署坑](./akasha-web-sync-git-deploy-pitfalls.md) - webhook 调用的 sync/build 过程依赖。
- [宝塔 Nginx SSL 配置文件冲突处理](./bt-nginx-ssl-config-conflict.md) - HTTPS server 块与宝塔 SSL 面板配置问题。
- [VitePress 宝塔 Nginx 部署 403/404 与 cleanUrls 刷新修复](./vitepress-nginx-deploy-403-cleanurls.md) - 同站点 Nginx 静态路径配置。

### 验证记录

- [2026-02-07] pm2 启动 webhook 服务成功，GitHub webhook 配置待完成。
- [2026-02-07] GitHub webhook 两个仓库均配置完成（HTTP、JSON、push only），delivery 返回 200。
- [2026-02-07] 发现 webhook.mjs 没有 git pull 自身代码，已修复并手动首次部署。
- [2026-02-07] HTTPS 反向代理验证：GitHub Recent Deliveries 显示 ping 事件返回 200 + `{"message":"pong"}`。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---
