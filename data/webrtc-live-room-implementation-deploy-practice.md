# 浏览器 WebRTC 群聊直播从实现到部署实践

**标签**：#web #network #deployment #troubleshooting #hdr #experience
**来源**：实践总结（已脱敏）
**收录日期**：2026-06-29
**来源日期**：2026-06-28
**更新日期**：2026-06-29
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（本地实现 + 公网部署 + 多端实测）
**适用版本**：Node.js 18+ / 原生 WebSocket / Browser WebRTC mesh / Nginx HTTPS 反向代理 / PM2 / coturn

### 概要

一个浏览器群聊直播 PoC 从空项目到公网基本可用，关键闭环不是“Node 服务启动”，而是实现、信令、屏幕捕获、TURN、防火墙、Nginx 子路径、PM2 发布和公网双端音视频验证全部打通。WebRTC 项目的上线标准应定义为“公网 HTTPS 双端真实观看成功”，而不是进程在线。

### 内容

#### 目标与技术边界

目标是做一个接近 QQ 群房间感的群聊直播页面：用户进入同一个房间后可聊天、看到成员、识别房主、复制邀请链接，并能共享屏幕给其他成员观看游戏画面。

本轮实践采用最小可验证架构：

- Node.js 只负责静态文件、房间状态、聊天和 WebRTC 信令中继。
- 浏览器端负责屏幕捕获、WebRTC peer connection、视频播放、画质与音频交互。
- 媒体传输采用 WebRTC mesh，不引入 SFU。
- 房间、成员和最近聊天历史放在内存中，不接数据库。
- 通过 Nginx 在 HTTPS 子路径下反向代理 Node 服务。
- 通过 PM2 管理 Node 进程。
- 通过 coturn/TURN 解决公网和移动端 NAT 穿透。

这个取舍适合小房间 PoC。它不适合直接扩展为大规模高码率直播平台，因为 mesh 下每个观众都会消耗主播一份上行。

#### 实现阶段

第一阶段先搭建无依赖项目骨架：

- `src/server.js`：HTTP 静态文件服务、原生 WebSocket 握手、房间和成员状态、聊天广播、信令转发。
- `public/index.html`：单页房间 UI。
- `public/styles.css`：桌面和移动端布局。
- `public/app.js`：浏览器状态机、WebRTC、屏幕共享、播放控制。
- `scripts/smoke-ws.js`：用原始 TCP/WebSocket 客户端做协议冒烟测试。

服务端消息协议按最小集合设计：

| 消息 | 方向 | 作用 |
|---|---|---|
| `hello` | server -> client | 分配连接 ID，并下发 ICE 配置。 |
| `join` | client -> server | 加入房间，携带昵称、房间号和浏览器稳定身份。 |
| `joined` | server -> client | 返回 selfId、roomId、ownerId、成员列表和历史消息。 |
| `peer-joined` / `peer-left` | server -> client | 广播成员变化和房主变化。 |
| `chat` | 双向 | 广播群聊消息。 |
| `stream-state` | client -> server -> room | 广播直播状态、画质档位和码率。 |
| `signal` | client -> server -> target | 透明转发 WebRTC offer、answer、candidate 和观众画质请求。 |
| `client-log` | client -> server | 把浏览器端 WebRTC 状态摘要写入 PM2 日志，辅助排查黑屏和移动端问题。 |

实现中补齐的关键语义：

1. 房间号归一化：去掉开头 `#`，统一大小写，空格和非法字符折叠，避免同一个邀请词进入平行空房间。
2. 同浏览器去重：浏览器生成并持久化 `clientKey`，服务端用它替换旧连接，避免同一个人刷新后显示两份成员。
3. 房主语义：最早加入且仍在线的成员为房主，离开后自动转移。
4. 成员直播状态：成员列表显示在线、自己、房主、LIVE、画质和码率。
5. 本地系统提示：开始/停止共享、捕获失败等只作为本地提示，不写入服务器历史。

#### 前端交互阶段

页面从普通表单改成“游戏房间控制台”结构：

- 顶部为房间状态栏：品牌、连接状态、房间号、在线人数、房主、直播路数、邀请按钮。
- 首次进入显示加入面板；加入后隐藏大表单，只保留房间状态和核心操作。
- 主区域为左成员、中直播舞台、右群聊。
- 移动端以舞台优先，成员和群聊使用底部切换面板。
- 底部直播控制条包含共享、停止、画质、码率、共享/播放音频。

后续 PC 布局问题证明：静态语法检查无法发现真实布局错位。加入房间后如果 entry 面板 `display:none`，外层 grid 还保留三行，会在桌面端留下空白行；修复方式是根据 joined 状态把 shell 行数折叠为“顶部栏 + 工作区”。

#### WebRTC 与屏幕共享阶段

浏览器端建立每个成员之间的 `RTCPeerConnection`。服务端只转发信令，不接触媒体流。

主播开始共享时：

1. 打开共享前确认面板。
2. 检查是否支持 `navigator.mediaDevices.getDisplayMedia`。
3. 检查是否处于 HTTPS 或 localhost 这类安全上下文。
4. 请求屏幕流。
5. 对视频 track 尝试应用分辨率和帧率约束。
6. 对每个 peer 的 video sender 应用码率和帧率上限。
7. 广播 `stream-state`。

画质分两层处理：

- 捕获约束：尽量要求 720p30、1080p30 或 1080p60。
- 发送约束：通过 `RTCRtpSender.setParameters()` 设置 `maxBitrate`、`maxFramerate` 等发送端限制。

观众选择画质时，不直接修改全局状态，而是通过信令向主播请求该观众对应 sender 的画质/码率。mesh 下每个观众有独立 sender，这样一个观众请求高码率不会强制影响其他观众。

#### 音频处理阶段

共享音频不能只看复选框，必须以实际 `MediaStream.getAudioTracks()` 为准。

关键结论：

- `getDisplayMedia({ audio: true })` 只是请求音频，不保证浏览器返回音轨。
- Safari/macOS 通常无法把系统音频交给网页。
- Chrome/Edge 也依赖用户选择的共享源、屏幕选择器中的音频开关和系统权限。
- 观众端必须默认静音远端视频，用户点击“播放声音”后再解除静音，否则容易被浏览器自动播放策略拦截。
- 如果远端 stream 没有 live audio track，观众端应禁用播放声音并提示“主播端没有音频轨道”。

最终 UI 应显示真实状态：未请求音频、未采集到音频、音频已共享、无音频轨道、可播放、声音已开。

#### HDR 问题处理阶段

HDR 过曝的根因在捕获侧，而不是观众端播放或 CSS 滤镜。

实践中尝试过“兼容 HDR”的方向，但最终结论是：浏览器 `getDisplayMedia` 没有可靠的 HDR 转 SDR tone mapping 约束。如果 Windows HDR 或游戏 HDR 输出在浏览器捕获时已经过曝/裁剪，WebRTC 发送后无法恢复高光细节。

正确做法是：

- 删除误导性的 HDR 兼容开关、滤镜和 canvas SDR 转换补丁。
- 在 Windows + 高动态范围显示环境下阻止开始共享。
- 明确提示主播先关闭 Windows HDR 和游戏 HDR，刷新页面后再共享。

这类问题应修根因，不应通过观众端滤镜掩盖。

#### 本地验证阶段

本地验证至少分三层：

```bash
npm run check
```

语法检查覆盖 Node 服务、浏览器脚本和 smoke 脚本。

```bash
npm start
npm run smoke:ws
```

WebSocket 冒烟测试应覆盖：

- 加入房间。
- 房主识别。
- 房主离开后转移。
- 房间号归一化。
- 聊天广播。
- 直播状态广播。
- 码率字段广播。
- 观众画质/码率请求信令。
- 同浏览器 `clientKey` 重复连接替换。

UI 和 WebRTC 还必须做真实浏览器验证：

- 桌面双页面加入同一房间。
- 主播共享屏幕，观众能看到画面。
- 点击直播画面不应导致 video DOM 重建后卡住。
- 新观众在主播直播中加入，应能协商并同步到画面。
- 移动端切换舞台、成员、群聊时，视频不被输入框遮挡。
- 观众端音频按钮状态与实际 audio track 一致。

#### 服务器配置阶段

服务器侧采用 Node 本地端口 + PM2 + Nginx HTTPS 反代的结构：

```text
Browser HTTPS <public-domain>/<app-subpath>/
        -> Nginx 443
        -> http://127.0.0.1:<node-port>/
        -> Node.js app
```

部署时不要把 Node 服务直接暴露到公网。公网只开放 80/443 和 WebRTC/TURN 必要端口。

Nginx 子路径反代重点：

- `<app-subpath>/` 反代到 Node 根路径。
- `<app-subpath>/ws` 必须正确转到 Node 的 `/ws`。
- WebSocket 反代必须显式设置 `Upgrade` 和 `Connection`。
- 静态资源可使用 `no-store`，减少部署后浏览器缓存旧 JS/CSS 的误判。

#### TURN 与防火墙阶段

公网和移动端黑屏的常见根因不是前端，而是 NAT 穿透失败。

TURN 可用性需要同时满足：

1. coturn 服务运行。
2. Node `/ice-config` 下发 TURN 地址和凭证。
3. 云服务器安全组/防火墙开放 TURN 端口。
4. 浏览器实际 ICE candidate 出现 relay。
5. 观众端 `iceConnectionState` 进入 connected/completed。
6. 视频进入 `video-ready` 或有帧解码统计。

端口经验：

```text
3478/udp
3478/tcp
49160-49200/udp
```

如启用 TCP relay 或特殊网络，还应按 coturn 配置开放对应 TCP relay 范围。

验证不能停在“coturn 进程在线”。必须做 forced relay-only 测试，确认浏览器实际使用 `candidateType: relay` 并能播放视频。

#### 发布阶段

推荐使用 release 目录 + current 软链，不直接覆盖运行目录：

```text
<app-root>/releases/<release-id>
<app-root>/current -> <app-root>/releases/<release-id>
```

打包时 macOS 需要避免 AppleDouble 文件：

```bash
COPYFILE_DISABLE=1 tar -czf <tmp-archive> package.json public src scripts
```

远端发布流程：

```bash
mkdir -p <app-root>/releases/<release-id>
tar -xzf <tmp-archive> -C <app-root>/releases/<release-id>
cd <app-root>/releases/<release-id>
npm run check
ln -sfn <app-root>/releases/<release-id> <app-root>/current
pm2 restart <pm2-process> --update-env
```

PM2 重启会断开当前房间。当前 PoC 的房间和消息都在内存中，重启后用户需要刷新重进。

#### 远端验证阶段

部署后至少执行：

```bash
curl -fsS http://127.0.0.1:<node-port>/health
cd <app-root>/current
HOST=127.0.0.1 PORT=<node-port> npm run smoke:ws
curl -fsS https://<public-domain>/<app-subpath>/health
pm2 logs <pm2-process> --lines 20 --nostream
```

公网 UI 改动还要验证：

- 公网页面加载的是新 HTML/CSS/JS。
- `<app-subpath>/ws` 连接成功。
- 两个公网客户端能进入同一房间。
- 主播共享后观众有画面。
- 观众能请求画质和码率。
- 有实际音轨时，观众点击播放声音后能听到。
- 手机端不长期停在“同步中/连接中”。
- PM2 日志没有持续的信令错误、ICE failed 或 video sync stalled。

#### 常见失败模式

| 现象 | 根因 | 处理方式 |
|---|---|---|
| 同一人出现两次 | 只有昵称，没有稳定浏览器身份 | 使用 `clientKey` 做同浏览器去重。 |
| 同房间号进了空房间 | 房间 ID 未归一化 | 服务端和客户端统一 normalize room id。 |
| 没有房主概念 | 房间缺少 owner 语义 | 使用最早 joinedAt 的在线成员作为房主并在离开后转移。 |
| 观众黑屏 | track 到达但未 unmute 或没有首帧 | 等待 track unmute 和 video ready，不要过早渲染黑 video。 |
| 点画面后卡住 | 重渲染替换了 live video DOM | 使用 stage signature，普通状态变化只 attach stream，不重建 video。 |
| 手机一直同步中 | 没有可用 TURN relay | 开放 TURN 端口并用 relay-only 测试验证。 |
| 开了共享音频但观众听不到 | 主播实际没有采集到 audio track | 根据实际 audio track 提示，不相信 checkbox。 |
| Chrome 选择程序窗口无反应 | 程序窗口捕获路径超时 | 提供兼容捕获模式和整屏 fallback。 |
| HDR 画面过曝 | 捕获侧已裁剪高光 | 阻止 HDR 环境共享，要求先关闭系统和游戏 HDR。 |
| PC 端下方大片空白 | joined 状态 grid 行数未折叠 | 加入后把 shell grid 改为顶部栏 + 工作区。 |

#### 架构边界

当前架构适合小房间 PoC，不适合生产级多人游戏直播：

- 无账号体系和权限系统。
- 无持久化消息和离线历史。
- PM2 重启会丢失房间状态。
- mesh 下主播上行约等于单观众码率乘以观众数。
- 浏览器系统音频、HDR 捕获、自动播放仍受平台策略限制。
- 多人高码率观看应迁移到 SFU，如 LiveKit、mediasoup 或 Janus。

最终经验：WebRTC 群聊直播项目的完成标准必须是公网双端真实观看成功，包含 HTTPS、WebSocket、TURN、ICE、track unmute、video frame、audio track 和移动端验证。只看到 PM2 online 或 `/health` 返回 ok，不能宣称部署完成。

### 关键代码

#### WebSocket 子路径推导

```javascript
function webSocketPath() {
  const pathname = window.location.pathname || "/";
  const lastSegment = pathname.split("/").pop() || "";
  const basePath = pathname.endsWith("/")
    ? pathname
    : lastSegment.includes(".")
      ? pathname.replace(/[^/]*$/, "")
      : `${pathname}/`;
  return `${basePath.replace(/\/$/, "")}/ws` || "/ws";
}
```

#### 发送端码率限制

```javascript
async function applySenderLimits(sender, bitrate, maxFramerate) {
  if (!sender.track || sender.track.kind !== "video") return;
  const parameters = sender.getParameters();
  parameters.encodings = parameters.encodings?.length ? parameters.encodings : [{}];
  parameters.encodings[0].maxBitrate = bitrate;
  parameters.encodings[0].maxFramerate = maxFramerate;
  await sender.setParameters(parameters);
}
```

#### Nginx WebSocket 反代模板

```nginx
location <app-subpath>/ws {
    proxy_pass http://127.0.0.1:<node-port>/ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
}
```

#### 发布命令模板

```bash
COPYFILE_DISABLE=1 tar -czf <tmp-archive> package.json public src scripts
mkdir -p <app-root>/releases/<release-id>
tar -xzf <tmp-archive> -C <app-root>/releases/<release-id>
cd <app-root>/releases/<release-id>
npm run check
ln -sfn <app-root>/releases/<release-id> <app-root>/current
pm2 restart <pm2-process> --update-env
```

### 参考链接

- [MDN MediaDevices.getDisplayMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia) - 屏幕捕获 API、安全上下文、用户授权和异常边界。
- [MDN RTCRtpSender.setParameters](https://developer.mozilla.org/en-US/docs/Web/API/RTCRtpSender/setParameters) - WebRTC sender 编码参数、码率和帧率控制。
- [Nginx WebSocket proxying](https://nginx.org/en/docs/http/websocket.html) - WebSocket 反向代理需要显式传递 Upgrade/Connection。
- [PM2 Process Management](https://pm2.keymetrics.io/docs/usage/process-management/) - PM2 进程启动、重启和 `--update-env` 语义。

### 相关记录

- [AI Agent 介入远程服务器操作的脱敏安全流程](./remote-server-agent-operation-sop.md) - 远程服务器操作、脱敏和验证门禁。
- [Akasha Webhook PM2 守护与 HTTPS 反向代理](./akasha-webhook-pm2-https-proxy.md) - Node 服务经 PM2 守护并由 Nginx HTTPS 反代的相邻经验。
- [宝塔 Nginx SSL 配置文件冲突处理](./bt-nginx-ssl-config-conflict.md) - 宝塔/Nginx/SSL 配置冲突排查。
- [VitePress 宝塔 Nginx 部署 403/404 与 cleanUrls 刷新修复](./vitepress-nginx-deploy-403-cleanurls.md) - Nginx 静态站和路由验证经验。
- [ACES Tone Mapping](./aces-tone-mapping.md) - HDR 到 LDR 色调映射的图形学背景。

### 验证记录

- [2026-06-29] 初次记录。写入前已执行 `git pull origin main`，并运行 `python3 references/scripts/validate_records.py`，结果为 `No issues found.`。
- [2026-06-29] 本地查重：阿卡西 `data/*.md` 中未发现浏览器群聊直播 PoC、WebRTC mesh、TURN 公网观看、观众画质请求、HDR 捕获阻断的专项记录；仅发现 PM2/Nginx/宝塔/服务器操作/HDR 色彩等相邻记录，已在“相关记录”中引用。
- [2026-06-29] 外部核对：MDN `getDisplayMedia`、MDN `RTCRtpSender.setParameters`、Nginx WebSocket proxying、PM2 Process Management 与本次实践结论一致。
- [2026-06-29] 脱敏审查：原始实践涉及真实公网域名、服务器 IP、远端目录、本机绝对路径和 PM2 进程名；正式记录已替换为 `<public-domain>`、`<server-ip>`、`<app-root>`、`<local-project>`、`<pm2-process>`、`<app-subpath>` 等占位符，不写入可直接定位个人资产的信息。

---
