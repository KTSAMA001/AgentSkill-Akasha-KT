# VitePress 宝塔 Nginx 部署 403/404 与 cleanUrls 刷新修复

**标签**：#web #vitepress #experience #deployment #troubleshooting
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-07
**来源日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：VitePress 1.x + Nginx 1.26 + 宝塔面板 9.x + Alibaba Cloud Linux 3

### 概要

VitePress 静态站部署到宝塔 Nginx 时，403 多由真实目录缺少 `index.html` 导致，cleanUrls 刷新 404 则需要 Nginx `try_files` 显式尝试 `.html` 后缀。站点 `root` 必须指向 `.vitepress/dist`。

### 内容

#### 问题/场景

- 将 VitePress 项目部署到服务器，站点通过宝塔面板管理 Nginx。
- 初期出现 404/403：
  - 站点根目录路径迁移后仍然异常。
  - 某些分类路径访问返回 403。
- 后续启用 `cleanUrls: true` 后，站内 SPA 跳转正常，但详情页刷新返回 404。

#### Nginx root 必须指向构建产物目录

Nginx 配置核心点：

- `root` 必须指向 `.vitepress/dist`。
- `index index.html;` 必须存在。

#### 403 根因：目录存在但没有 index.html

错误日志典型表现：

```text
directory index of ".../dist/experiences/ai/" is forbidden
```

这表示 Nginx 命中了一个真实目录，但目录下缺少 `index.html`。

推荐修复：在内容同步阶段自动补齐每个分类目录的 `index.md`，让 VitePress 自动生成对应目录的 `index.html`。

实现方式：

- 在站点工程的同步脚本中，同步完 `experiences/knowledge/ideas` 后递归检查子目录。
- 如果某目录没有 `index.md`，自动生成一个目录页。
- 目录页列出该目录下的所有 `.md` 文件链接。

这样无需污染原始笔记仓库，也能保证 Web 访问目录路径时有落地页。

#### 目录权限修复

```bash
chmod -R 755 /www/wwwroot/AkashaRecord-Web
chown -R www:www /www/wwwroot/AkashaRecord-Web
/www/server/nginx/sbin/nginx -s reload
```

#### cleanUrls 刷新 404

VitePress 配置 `cleanUrls: true` 后，构建产物是 `xxx.html`，但页面 URL 显示为 `/records/xxx`。站内 SPA 跳转由客户端路由处理没问题，但直接访问或浏览器刷新时，Nginx 默认不会尝试加 `.html` 后缀。

排查过程：

- `cleanUrls: true` 从项目早期就存在，不是新改动引入。
- 问题之前没暴露，是因为一直通过首页 SPA 导航进入文档。
- `curl -sI /records/xxx` 返回 404。
- `curl -sI /records/xxx.html` 返回 200。

修复方式是在 Nginx `server` 块中添加：

```nginx
# VitePress cleanUrls 支持
location / {
    try_files $uri $uri.html $uri/ /404.html;
}
```

查找顺序：

1. `/records/xxx` 精确文件。
2. `/records/xxx.html`。
3. `/records/xxx/` 目录。
4. `/404.html`。

`location /` 可放在 `location /webhook` 之前，不影响更具体路径的优先匹配。

#### 诊断备注

诊断 403/404 时，优先看：

- Nginx 站点 error log。
- `ls -l` 验证 dist 内是否存在 `index.html`。

如果某路径既可能是目录，也可能是同名 HTML（cleanUrls 场景），`try_files` 顺序会影响行为；但最稳妥还是让目录真实存在 `index.html`。

### 关键代码

见“内容”中的 Nginx `try_files` 配置和目录权限修复命令。

### 相关记录

- [CI/CD 持续集成与持续交付术语](./cicd-continuous-integration-delivery-terms.md) - 解释 CI/CD 概念。
- [Akasha Web 同步脚本与 Git 部署坑](./akasha-web-sync-git-deploy-pitfalls.md) - 同步脚本层面的部署容错。
- [Akasha Webhook PM2 守护与 HTTPS 反向代理](./akasha-webhook-pm2-https-proxy.md) - webhook 自动构建入口。

### 验证记录

- [2026-02-07] 通过 Nginx error.log 定位 403 根因：目录缺 index。
- [2026-02-07] 通过同步脚本自动生成目录 index.md 的策略稳定解决。
- [2026-02-07] 服务器端 GitHub 拉取失败属于网络问题，脚本容错逻辑生效。
- [2026-05-25] 补充关联：新增开发工具术语词条后，反向补充 CI/CD 术语解释引用。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---
