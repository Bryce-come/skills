---
name: web-access
license: MIT
github: https://github.com/eze-is/web-access
description:
  所有联网操作必须通过此 skill 处理，包括：搜索、网页抓取、登录后操作、网络交互等。
  触发场景：用户要求搜索信息、查看网页内容、访问需要登录的网站、操作网页界面、抓取社交媒体内容（小红书、微博、推特等）、读取动态渲染页面、以及任何需要真实浏览器环境的网络任务。
metadata:
  author: 一泽Eze
  version: "2.5.0"
---

# web-access Skill

## 前置检查

在开始联网操作前，先检查 CDP 模式可用性：

```bash
node "${CLAUDE_SKILL_DIR}/scripts/check-deps.mjs"
```

未通过时引导用户完成设置：
- **Node.js 22+**：必需（使用原生 WebSocket）。版本低于 22 可用但需安装 `ws` 模块。
- **Chrome remote-debugging**：在 Chrome 地址栏打开 `chrome://inspect/#remote-debugging`，勾选 **"Allow remote debugging for this browser instance"** 即可，可能需要重启浏览器。

检查通过后并必须在回复中向用户直接展示以下须知，再启动 CDP Proxy 执行操作：

```
温馨提示：部分站点对浏览器自动化操作检测严格，存在账号封禁风险。已内置防护措施但无法完全避免，Agent 继续操作即视为接受。
```

## 浏览哲学

**像人一样思考，兼顾高效与适应性的完成任务。**

执行任务时不会过度依赖固有印象所规划的步骤，而是带着目标进入，边看边判断，遇到阻碍就解决，发现内容不够就深入——全程围绕「我要达成什么」做决策。这个 skill 的所有行为都应遵循这个逻辑。

**① 拿到请求** — 先明确用户要做什么，定义成功标准：什么算完成了？需要获取什么信息、执行什么操作、达到什么结果？这是后续所有判断的锚点。

**② 选择起点** — 根据任务性质、平台特征、达成条件，选一个最可能直达的方式作为第一步去验证。一次成功当然最好；不成功则在③中调整。比如，需要操作页面、需要登录态、已知静态方式不可达的平台（小红书、微信公众号等）→ 直接 CDP

**③ 过程校验** — 每一步的结果都是证据，不只是成功或失败的二元信号。用结果对照①的成功标准，更新你对目标的判断：路径在推进吗？结果的整体面貌（质量、相关度、量级）是否指向目标可达？发现方向错了立即调整，不在同一个方式上反复重试——搜索没命中不等于"还没找对方法"，也可能是"目标不存在"；API 报错、页面缺少预期元素、重试无改善，都是在告诉你该重新评估方向。遇到弹窗、登录墙等障碍，判断它是否真的挡住了目标：挡住了就处理，没挡住就绕过——内容可能已在页面 DOM 中，交互只是展示手段。

**④ 完成判断** — 对照定义的任务成功标准，确认任务完成后才停止，但也不要过度操作，不为了"完整"而浪费代价。

## 联网工具选择

- **确保信息的真实性，一手信息优于二手信息**：搜索引擎和聚合平台是信息发现入口。当多次搜索尝试后没有质的改进时，升级到更根本的获取方式：定位一手来源（官网、官方平台、原始页面）。

| 场景 | 工具 |
|------|------|
| 搜索摘要或关键词结果，发现信息来源 | **WebSearch** |
| URL 已知，需要从页面定向提取特定信息 | **WebFetch**（拉取网页内容，由小模型根据 prompt 提取，返回处理后结果） |
| URL 已知，需要原始 HTML 源码（meta、JSON-LD 等结构化字段） | **curl** |
| 非公开内容，或已知静态层无效的平台（小红书、微信公众号等公开内容也被反爬限制） | **浏览器 CDP**（直接，跳过静态层） |
| 需要登录态、交互操作，或需要像人一样在浏览器内自由导航探索 | **浏览器 CDP** |

浏览器 CDP 不要求 URL 已知——可从任意入口出发，通过页面内搜索、点击、跳转等方式找到目标内容。WebSearch、WebFetch、curl 均不处理登录态。

**Jina**（可选预处理层，可与 WebFetch/curl 组合使用，由于其特性可节省 tokens 消耗，请积极在任务合适时组合使用）：第三方网络服务，可将网页转为 Markdown，大幅节省 token 但可能有信息损耗。调用方式为 `r.jina.ai/example.com`（URL 前加前缀，不保留原网址 http 前缀），限 20 RPM。适合文章、博客、文档、PDF 等以正文为核心的页面；对数据面板、商品页等非文章结构页面可能提取到错误区块。

进入浏览器层后，`/eval` 就是你的眼睛和手：

- **看**：用 `/eval` 查询 DOM，发现页面上的链接、按钮、表单、文本内容——相当于「看看这个页面有什么」
- **做**：用 `/click` 点击元素、`/scroll` 滚动加载、`/eval` 填表提交——像人一样在页面内自然导航
- **读**：用 `/eval` 提取文字内容，判断图片/视频是否承载核心信息——是则提取媒体 URL 定向读取或 `/screenshot` 视觉识别

浏览网页时，**先了解页面结构，再决定下一步动作**。不需要提前规划所有步骤。

### 补充：本地 Chrome 资源

用户指向**本人访问过的页面**（"我之前看的那个讲 X 的文章"、"上次打开过的 XX 面板"）或**组织内部系统**（"我们的 XX 平台"、"公司那个 YY 系统"等公网搜不到的目标）时，检索本地 Chrome 书签/历史：

```bash
node "${CLAUDE_SKILL_DIR}/scripts/find-url.mjs" [关键词...] [--only bookmarks|history] [--limit N] [--since 1d|7h|YYYY-MM-DD] [--sort recent|visits]
```

关键词空格分词、多词 AND，匹配 title + url（可省略）；`--since` / `--sort` 仅作用于历史；默认按最近访问倒序，`--sort visits` 按访问次数排序（适合"高频访问的网站"这类场景）。

### 程序化操作与 GUI 交互

浏览器内操作页面有两种方式：

- **程序化方式**（构造 URL 直接导航、eval 操作 DOM）：成功时速度快、精确，但对网站来说不是正常用户行为，可能触发反爬机制。
- **GUI 交互**（点击按钮、填写输入框、滚动浏览）：GUI 是为人设计的，网站不会限制正常的 UI 操作，确定性最高，但步骤多、速度慢。

根据对目标平台的了解来灵活选择方式。GUI 交互也是程序化方式的有效探测——通过一次真实交互观察站点的实际行为（URL 模式、必需参数、页面跳转逻辑），为后续程序化操作提供依据；同时当程序化方式受阻时，GUI 交互是可靠的兜底。

**站点内交互产生的链接是可靠的**：通过用户视角中的可交互单元（卡片、条目、按钮）进行的站点内交互，自然到达的 URL 天然携带平台所需的完整上下文。而手动构造的 URL 可能缺失隐式必要参数，导致被拦截、返回错误页面、甚至触发反爬。

## 浏览器 CDP 模式

通过 CDP Proxy 直连用户日常 Chrome，天然携带登录态，无需启动独立浏览器。
若无用户明确要求，不主动操作用户已有 tab，所有操作都在自己创建的后台 tab 中进行，保持对用户环境的最小侵入。不关闭用户 tab 的前提下，完成任务后关闭自己创建的 tab，保持环境整洁。

### 启动

```bash
node "${CLAUDE_SKILL_DIR}/scripts/check-deps.mjs"
```

脚本会依次检查 Node.js、Chrome 端口，并确保 Proxy 已连接（未运行则自动启动并等待）。Proxy 启动后持续运行。

### Proxy API

所有操作通过 curl 调用 HTTP API：

```bash
# 列出用户已打开的 tab
curl -s http://localhost:3456/targets

# 创建新后台 tab（自动等待加载）
curl -s "http://localhost:3456/new?url=https://example.com"

# 页面信息
curl -s "http://localhost:3456/info?target=ID"

# 执行任意 JS：可读写 DOM、提取数据、操控元素、触发状态变更、提交表单、调用内部方法
curl -s -X POST "http://localhost:3456/eval?target=ID" -d 'document.title'

# 捕获页面渲染状态（含视频当前帧）
curl -s "http://localhost:3456/screenshot?target=ID&file=/tmp/shot.png"

# 导航、后退
curl -s "http://localhost:3456/navigate?target=ID&url=URL"
curl -s "http://localhost:3456/back?target=ID"

# 点击（POST body 为 CSS 选择器）— JS el.click()，简单快速，覆盖大多数场景
curl -s -X POST "http://localhost:3456/click?target=ID" -d 'button.submit'

# 真实鼠标点击 — CDP Input.dispatchMouseEvent，算用户手势，能触发文件对话框
curl -s -X POST "http://localhost:3456/clickAt?target=ID" -d 'button.upload'

# 文件上传 — 直接设置 file input 的本地文件路径，绕过文件对话框
curl -s -X POST "http://localhost:3456/setFiles?target=ID" -d '{"selector":"input[type=file]","files":["/path/to/file.png"]}'

# 滚动（触发懒加载）
curl -s "http://localhost:3456/scroll?target=ID&y=3000"
curl -s "http://localhost:3456/scroll?target=ID&direction=bottom"

# 关闭 tab
curl -s "http://localhost:3456/close?target=ID"
```

### 页面内导航

两种方式打开页面内的链接：

- **`/click`**：在当前 tab 内直接点击用户视角中的可交互单元，简单直接，串行处理。适合需要在同一页面内连续操作的场景，如点击展开、翻页、进入详情等。
- **`/new` + 完整 URL**：使用目标链接的完整地址（包含所有URL参数），在新 tab 中打开。适合需要同时访问多个页面的场景。

很多网站的链接包含会话相关的参数（如 token），这些参数是正常访问所必需的。提取 URL 时应保留完整地址，不要裁剪或省略参数。

### 媒体资源提取

判断内容在图片里时，用 `/eval` 从 DOM 直接拿图片 URL，再定向读取——比全页截图更高效。视频同理：先取 URL，如需分析画面内容再 `/screenshot` 截帧。

```bash
# 提取页面所有图片 URL
curl -s -X POST "http://localhost:3456/eval?target=ID" -d 'JSON.stringify([...document.querySelectorAll("img")].map(img => ({src: img.src, alt: img.alt})))'
```

### DOM 边界穿透

`eval` 递归遍历可穿透 Shadow DOM、iframe 等选择器不可跨越的边界。当标准 CSS 选择器无法定位元素时，用 eval 递归查询往往能找到。

```bash
# 穿透 Shadow DOM 查找元素
curl -s -X POST "http://localhost:3456/eval?target=ID" -d '
function findInShadow(root, selector) {
  const found = root.querySelectorAll(selector);
  if (found.length) return [...found];
  for (const el of root.querySelectorAll("*")) {
    if (el.shadowRoot) {
      const result = findInShadow(el.shadowRoot, selector);
      if (result.length) return result;
    }
  }
  return [];
}
JSON.stringify(findInShadow(document, "your-selector").map(el => el.textContent));
'
```

### 站点经验积累

按域名存储操作经验，跨 session 复用。经验文件位于 `${CLAUDE_SKILL_DIR}/sites/` 目录下，以域名命名。

当前已有经验站点：
- `xiaohongshu.com` — 小红书（xsec_token 机制、创作者平台状态校验、暂存草稿流程）

新增站点经验时，创建 `sites/<domain>.md`，记录：
- URL 模式（哪些路径可用、哪些会跳转）
- 平台特征（反爬机制、必需参数、常见陷阱）
- 已知操作路径（如发布流程、搜索流程）

## 并行分治

多目标时分发子 Agent 并行执行，共享一个 Proxy，tab 级隔离。

子 Agent prompt 写法：
```
你正在使用 web-access skill 执行联网任务。当前 CDP Proxy 已运行在 localhost:3456，直接使用 curl 调用 API 即可，无需再次启动。

任务：...
```

**注意**：向子 Agent 描述任务时，避免用动词暗示具体执行方式（如"搜索"、"抓取"），只说明要获取什么信息、达成什么结果。让子 Agent 自己判断最佳工具组合。

## 平台错误提示不可信

平台返回的"内容不存在"、"访问受限"等提示可能是访问方式问题，而非内容本身问题。尝试不同工具或路径验证：
- WebFetch 报 403 → 试试 CDP
- CDP 显示"内容已删除" → 试试 curl 抓原始 HTML
- 搜索不到 → 试试直接构造 URL 访问
