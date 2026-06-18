# GitLab 私有分组无法无认证枚举全部仓库

**标签**：#git #network #experience #credential #pat #troubleshooting
**来源**：实践总结 + GitLab 官方文档
**收录日期**：2026-06-18
**来源日期**：2026-06-18
**更新日期**：2026-06-18
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（官方文档 + 脱敏实测）
**适用版本**：GitLab REST API v4 / GitLab Self-Managed

### 概要

GitLab 的分组项目 API 可以列出指定分组下的项目，并可通过 `include_subgroups=true` 包含子分组项目；但未认证访问时只返回公开项目。对于私有或内部可见的分组，想获取完整仓库列表必须使用具备权限的认证方式，浏览器已登录只是使用 session cookie 认证，不等于无认证访问。

### 内容

#### 问题场景

希望只通过 GitLab 分组 URL 获取该分组及其子分组下的全部仓库信息，而不使用访问令牌。典型触发点是浏览器中能打开分组页面，容易误以为脚本或 API 也能在无认证状态下枚举仓库。

#### 结论

- 只靠分组 URL 无认证访问时，GitLab 只会返回 public group / public project 能公开暴露的数据。
- 对 private 或 internal 分组，`GET /groups/:id/projects` 仍然是正确方向，但必须带上可访问该分组的身份认证。
- 浏览器登录态可让 GitLab Web 前端用 session cookie 访问 API；这属于 cookie 认证，不是“无 token / 无认证”。
- 如果目标只是读取仓库清单，优先使用最小权限认证，例如只授予 `read_api` 的 Personal Access Token、Group Access Token，或由组织策略允许的 OAuth/session 方式。
- `CI_JOB_TOKEN` 只适用于 GitLab 明确支持的特定 API 场景，不应默认替代通用 API token。
- Deploy Token 不能用于 GitLab public API，不适合列分组项目。

#### 推荐 API

使用完整分组路径时，需要把 `/` URL 编码为 `%2F`：

```text
GET https://<gitlab-host>/api/v4/groups/<url-encoded-group-path>/projects?include_subgroups=true&per_page=100
```

关键参数：

| 参数 | 作用 |
|------|------|
| `include_subgroups=true` | 包含子分组下的项目 |
| `per_page=100` | 单页尽量取满，仍需处理分页 |
| `page=<n>` | 拉取后续页 |
| `with_shared=false` | 如只关心该分组层级内项目，可排除共享到该分组的项目 |

判断结果时要注意：私有资源在无认证访问下可能返回 `404 Group Not Found`，这并不能单独证明路径写错；需要结合页面是否跳登录、公开分组搜索是否为空、以及认证后是否可访问来判断。

#### 安全取舍

- 不要把 token 写进 Git remote URL、脚本正文、提交记录、聊天记录或知识库。
- 脚本中优先通过环境变量、凭据管理器或交互式隐藏输入传递 token。
- 需要自动化时，优先申请范围最小、有效期较短、可撤销的 token。
- 如果通过浏览器 cookie 复用登录态，应先确认团队安全规范；cookie 泄露风险通常高于只读短期 token。

### 关键代码

无认证探测公开可见性：

```powershell
curl.exe -sS -L -o NUL -w "http_code=%{http_code}; effective_url=%{url_effective}`n" `
  "https://<gitlab-host>/<group-path>"

curl.exe -sS `
  "https://<gitlab-host>/api/v4/groups/<url-encoded-group-path>/projects?include_subgroups=true&per_page=100"
```

使用只读 API token 获取完整清单：

```powershell
$headers = @{ "PRIVATE-TOKEN" = $env:GITLAB_READ_API_TOKEN }
$uri = "https://<gitlab-host>/api/v4/groups/<url-encoded-group-path>/projects?include_subgroups=true&per_page=100"
Invoke-RestMethod -Headers $headers -Uri $uri
```

使用已登录的 `glab` 查询：

```powershell
glab api --hostname <gitlab-host> `
  "groups/<url-encoded-group-path>/projects?include_subgroups=true&per_page=100"
```

### 参考链接

- [GitLab Groups API](https://docs.gitlab.com/api/groups/) - `GET /groups/:id/projects`、未认证只返回 public projects、`include_subgroups` 参数。
- [GitLab REST API authentication](https://docs.gitlab.com/api/rest/authentication/) - API 认证方式、access token、session cookie、CI_JOB_TOKEN 与 Deploy Token 边界。
- [GitLab Personal Access Tokens](https://docs.gitlab.com/user/profile/personal_access_tokens/) - PAT 的创建、权限范围与有效期管理。

### 相关记录

- [Git HTTPS 失败切换 SSH](./git-https-fail-switch-ssh.md) - GitLab 仓库访问方式与认证排查的相邻经验。
- [Docker 容器内 Git 认证持久化](./docker-container-git-auth-persist.md) - 自动化环境中避免把 token 写入 remote URL 的相邻经验。

### 验证记录

- [2026-06-18] 本地查重：Akasha `data/*.md` 中未发现“GitLab 分组项目枚举、`include_subgroups` 与无认证限制”的直接记录；仅发现 Git 凭据、GitLab HTTPS/SSH、CI/CD 与提交规范等相邻记录，因此新增独立经验记录。
- [2026-06-18] 官方核对：GitLab Groups API 文档确认 `GET /groups/:id/projects` 可列分组项目，未认证时只返回 public projects，并支持 `include_subgroups`；REST API authentication 文档确认多数 API 需要认证或仅返回公开数据，并列出 access token、session cookie、CI_JOB_TOKEN 等认证方式。
- [2026-06-18] 脱敏实测：对 `<gitlab-host>/<group-path>/<target-group>` 做无认证访问时，页面响应跳转到登录页；分组详情 API 返回 `404 Group Not Found`；公开分组搜索返回空数组。该现象支持“目标分组未公开，无法无认证枚举全部仓库”的判断。
- [2026-06-18] 脱敏审查：真实内网域名、组织/业务分组路径、目标分组名和项目名均已替换为占位符；未写入账号、邮箱、token、Cookie、API key、完整内部 URL 或本机绝对路径。

---
