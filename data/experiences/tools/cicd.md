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

~~VitePress 默认不渲染 Mermaid，需要引入 `vitepress-plugin-mermaid`。~~

**更正（2026-02-07）**：`vitepress-plugin-mermaid@2.0.17` 与 VitePress 1.6.4 存在严重兼容性问题，会导致：

- 启动时报 `Failed to resolve dependency: vitepress > @vue/devtools-api, present in 'optimizeDeps.include'`
- 页面白屏（JS 无法加载）
- 即使手动安装 `@vue/devtools-api` 和 `@vueuse/core` 也无法解决

**最终方案**：卸载 `vitepress-plugin-mermaid`，改用客户端 Mermaid 组件（自定义 Vue 组件 + `mermaid` npm 包），在 VitePress 主题中注册为全局组件。

7) **`npx` 缓存陷阱导致白屏**

直接运行 `npx vitepress dev` 时，npx 可能使用全局缓存中的旧版/残缺 VitePress（路径指向 `~/.npm/_npx/...`），其 `optimizeDeps` 配置与本地 `node_modules` 不匹配，导致客户端 JS 无法加载（白屏）。

诊断方法：`curl -6 http://localhost:<port>/` 查看 HTML 中的 `<script>` 路径，如果指向 `/@fs/Users/.../.npm/_npx/...` 就说明用的是 npx 缓存版本。

**解决**：
- 使用 `npm run dev`（通过 package.json scripts 调用，自动用本地版本）
- 或直接 `./node_modules/.bin/vitepress dev`
- **不要**单独用 `npx vitepress dev`

8) **国内服务器访问 GitHub 不稳定**

阿里云等国内服务器拉取 GitHub 仓库经常超时或失败。

解决方案之一——配置 GitHub 镜像加速：

```bash
git config --global url."https://mirror.ghproxy.com/https://github.com/".insteadOf "https://github.com/"
```

同步脚本中也应添加容错逻辑：git pull 失败时不要中断流程，使用本地缓存继续构建。

**验证记录**：

- 2026-02-07 通过 Nginx error.log 定位 403 根因（目录缺 index）
- 2026-02-07 通过同步脚本自动生成目录 index.md 的策略稳定解决
- 2026-02-07 `vitepress-plugin-mermaid` 导致白屏，已移除并改用客户端组件方案
- 2026-02-07 发现 `npx` 缓存陷阱，改用本地 `node_modules/.bin/vitepress`
- 2026-02-07 服务器端 GitHub 拉取失败属于网络问题，脚本容错逻辑生效

**备注**：

- 诊断 403/404 时，优先看：
	- `/www/wwwlogs/<domain>.error.log`
	- `ls -l` 验证 dist 内是否存在 `index.html`
- 如果某路径既可能是“目录”也可能是“同名 html”（cleanUrls 场景），`try_files` 顺序会影响行为；但最稳妥还是让目录真实存在 `index.html`。
