# CI/CD 经验

> 持续集成/持续部署相关经验
> 
> 包含：GitHub Actions、Jenkins、自动化测试、部署流程等

---

## VitePress（静态站）在宝塔 Nginx 部署：403/404、路径迁移、Webhook 自动更新踩坑记录

**收录日期**：2026-02-07
**来源日期**：2026-02-07
**更新日期**：2026-02-07
**标签**：#vitepress #nginx #宝塔 #alicloud #alinux3 #webhook #git #部署
**状态**：✅ 已验证
**适用版本**：VitePress 1.x + Nginx 1.26 + 宝塔面板 9.x + Alibaba Cloud Linux 3

**问题/场景**：

- 将 VitePress 项目（AkashaRecord-Web）部署到阿里云服务器，站点 `akasha.ktsama.top` 通过宝塔面板管理 Nginx
- 初期出现 404/403：
	- 站点根目录路径从 `/root/...` 迁移到 `/www/wwwroot/...` 后仍然异常
	- 某些路径（如 `/experiences/ai/`、`/experiences/anthropic/`）访问返回 403
- 后续又遇到：
	- `dnf` 被错误的 Nginx 官方源干扰（把系统识别成“centos/3”，repodata 404）
	- `git` 报 `detected dubious ownership`（安全策略）
	- VitePress 配置启用 Mermaid 时因括号缺失导致构建失败

**解决方案/结论**：

1) **确保 Nginx `root` 指向 VitePress 构建产物目录**

Nginx 配置核心点：

- `root` 必须指向 `.vitepress/dist`
- `index index.html;`

2) **403 的根因：目录存在但没有 index.html，Nginx 禁止目录列表**

错误日志典型表现：

- `directory index of ".../dist/experiences/ai/" is forbidden`

这表示 Nginx 命中了一个真实目录（`/experiences/ai/`），但目录下缺少 `index.html`。

**推荐修复（更稳定）**：在内容同步阶段自动补齐每个分类目录的 `index.md`，让 VitePress 自动生成对应目录的 `index.html`。

实现方式：修改站点工程的同步脚本，在同步完 `experiences/knowledge/ideas` 后，递归检查子目录：

- 如果某目录没有 `index.md`，则自动生成一个“目录页”，列出该目录下的所有 `.md` 文件链接

这样无需污染原始笔记仓库，也能保证 Web 访问 `/xxx/` 永远有落地页。

3) **目录权限修复**（常规但必要）

```bash
chmod -R 755 /www/wwwroot/AkashaRecord-Web
chown -R www:www /www/wwwroot/AkashaRecord-Web
/www/server/nginx/sbin/nginx -s reload
```

4) **Git `dubious ownership`（安全策略）**

当使用 `root` 操作、但仓库目录属主是 `www`（或反过来）时，Git 会拒绝执行（防止目录劫持）。

解决：将目录加入 Git 信任列表

```bash
git config --global --add safe.directory /www/wwwroot/AkashaRecord-Web
git config --global --add safe.directory /www/wwwroot/AkashaRecord-Web/.akasha-repo
```

5) **Alibaba Cloud Linux 3 上 dnf 被错误 repo 搞坏**

现象：源地址类似 `http://nginx.org/packages/centos/3/x86_64/...` 返回 404，导致 `dnf makecache` 失败。

处理：禁用错误 repo（改名为 `.bak`），再清缓存：

```bash
dnf clean all
dnf makecache
```

6) **Mermaid 支持**

VitePress 默认不渲染 Mermaid，需要引入 `vitepress-plugin-mermaid`。

要点：

- 新增依赖后，服务器端部署必须 `npm install`
- 修改 `.vitepress/config.mts` 时要确保 `withMermaid(defineConfig(...))` 括号闭合，否则会报：
	- `Expected ")" but found end of file`

**验证记录**：

- 2026-02-07 通过 Nginx error.log 定位 403 根因（目录缺 index）
- 2026-02-07 通过同步脚本自动生成目录 index.md 的策略稳定解决
- 2026-02-07 Mermaid 插件集成后，代码块 ```mermaid``` 可正确渲染

**备注**：

- 诊断 403/404 时，优先看：
	- `/www/wwwlogs/<domain>.error.log`
	- `ls -l` 验证 dist 内是否存在 `index.html`
- 如果某路径既可能是“目录”也可能是“同名 html”（cleanUrls 场景），`try_files` 顺序会影响行为；但最稳妥还是让目录真实存在 `index.html`。
