# Alibaba Cloud Linux 3 Nginx 源导致 dnf 404（Legacy）

**标签**：#network #tools #experience #deployment #troubleshooting
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-07
**来源日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：Alibaba Cloud Linux 3 + dnf + Nginx 官方源

### 概要

旧聚合记录中保留了一条服务器包源问题：Alibaba Cloud Linux 3 上错误的 Nginx 官方源会把系统识别成 `centos/3`，导致 repodata 404 并干扰 `dnf makecache`。该片段与 VitePress/Git/Webhook 主线关联较弱，先拆为 narrow legacy 记录待二次整理。

### 内容

#### 现象

`dnf` 被错误的 Nginx 官方源干扰，源地址类似：

```text
http://nginx.org/packages/centos/3/x86_64/...
```

该地址返回 404，导致 `dnf makecache` 失败。

#### 处理

禁用错误 repo，例如将对应 repo 文件改名为 `.bak`，再清理缓存并重新生成缓存：

```bash
dnf clean all
dnf makecache
```

### 关键代码

见“内容”中的 `dnf clean all` 与 `dnf makecache`。

### 相关记录

- [Akasha Web 同步脚本与 Git 部署坑](./akasha-web-sync-git-deploy-pitfalls.md) - 同一部署过程中遇到的 Git 和构建链路问题。
- [VitePress 宝塔 Nginx 部署 403/404 与 cleanUrls 刷新修复](./vitepress-nginx-deploy-403-cleanurls.md) - 同一站点部署的 Nginx 静态访问问题。

### 验证记录

- [2026-02-07] 原聚合记录中记录了禁用错误 repo 并清缓存的处理方式。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论；该条为无法可靠归入六个建议主题的 legacy 片段，待二次整理。

---
