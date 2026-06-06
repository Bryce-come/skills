---
name: github-project-recon
description: >-
  快速通读 GitHub 下载/克隆的本地项目：识别技术栈、目录结构、入口、核心流程、
  项目目标、文档与测试完备度、优劣势与上手路径。Use when the user asks to quickly
  read, understand, onboard to, survey, or analyze a new GitHub repo, cloned project,
  open-source codebase, or asks 快速阅读/通读/了解新项目/项目调研/架构梳理.
---

# GitHub 项目快读（Project Recon）

## 目标

在**不盲目通读全部源码**的前提下，产出一份**可决策、可上手**的项目认知报告，覆盖：

- 项目做什么、为谁做、解决什么问题
- 技术栈、架构分层、模块边界
- 核心代码路径与主流程（请求/训练/批处理等）
- 如何安装、运行、测试、扩展
- 文档/测试/CI/安全/可维护性现状
- 优势、风险、缺口、建议的下一步

默认用**中文**写报告；用户指定语言时跟随用户。

---

## 触发后第一步：确认范围

向用户确认或从上下文推断：

| 项 | 默认 |
|----|------|
| 项目根目录 | 用户 @ 的路径；否则当前 workspace 根 |
| 深度 | **标准**（见下方模式） |
| 是否运行 | 仅当用户明确要求或需要验证「能否跑起来」 |
| 关注点 | 无则全量；有则优先（如 API、训练 pipeline、部署） |

**三种模式**（写入报告标题）：

| 模式 | 时间预算 | 适用 |
|------|----------|------|
| **Express** | ~15 分钟 | 选型、粗筛、对比多个 repo |
| **Standard** | ~30–45 分钟 | 入职、接手、课程作业调研 |
| **Deep** | 1 小时+ | 准备改造/贡献/生产接入；含运行验证与 git 历史 |

---

## 执行原则

1. **先文档后代码，先结构后细节**：README → 清单文件 → 目录树 → 入口 → 核心模块。
2. **证据驱动**：每个结论附路径/命令/片段引用；不确定标 `[待验证]`。
3. **并行侦察**：独立搜索（Glob/Grep/Read）并行执行；大仓库用 `Task` + `explore` 子 agent 分域扫描。
4. **不臆造**：未见 README/配置/测试时不写「有」；未见运行成功不写「可运行」。
5. **最小足够阅读**：单文件 >800 行只读头尾+关键函数；用 Grep 定位再精读。
6. **尊重用户规则**：未要求不改代码；未要求不 commit。

---

## 标准工作流（按序执行）

复制并跟踪进度：

```
Recon Progress:
- [ ] Phase 0: 范围与扫描脚本
- [ ] Phase 1: 表面情报（文档与清单）
- [ ] Phase 2: 结构与架构
- [ ] Phase 3: 核心逻辑与数据流
- [ ] Phase 4: 工程化与质量
- [ ] Phase 5: 运行验证（可选）
- [ ] Phase 6: 综合报告
```

### Phase 0：机器扫描（必做）

在项目根目录执行（将 `PROJECT_ROOT` 替换为实际路径）：

```bash
python scripts/scan_project.py "PROJECT_ROOT"
```

- 将 JSON 输出作为**客观基线**（文件规模、清单文件、CI、测试目录等）。
- 脚本失败时手动完成同等检查，并在报告中说明。

### Phase 1：表面情报（5–10 分钟）

**必读（存在则读）**，按优先级：

1. `README*` / `README.*` / `docs/` 索引页
2. `CONTRIBUTING*` / `CHANGELOG*` / `LICENSE*`
3. 依赖与构建：`package.json`, `pyproject.toml`, `requirements*.txt`, `Pipfile`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle*`, `Gemfile`, `composer.json`
4. 容器与部署：`Dockerfile*`, `docker-compose*`, `helm/`, `k8s/`, `terraform/`, `.github/workflows/`
5. 环境样例：`.env.example`, `config*.yaml`, `settings*.py`

**提取字段**：

- 一句话定位、目标用户、核心能力列表
- 声明的安装/运行命令 vs 仓库实际是否一致
- 版本要求（语言、框架、外部服务）
- 许可证与商业使用限制

### Phase 2：结构与架构（10–15 分钟）

1. **目录语义图**：结合 Phase 0 输出，归纳顶层目录职责（不要只列文件名）。
2. **架构风格判定**（多选）：Monolith / Modular monolith / Microservices / Serverless / Library-SDK / CLI / Batch-ML pipeline / Full-stack / Plugin 体系。
3. **分层识别**：Presentation → Application → Domain → Infrastructure；或 ML 项目的 data → features → train → eval → serve。
4. **入口点清单**（全部列出）：
   - Web：`main.py`, `app.py`, `server.*`, `routes/`, `controllers/`
   - CLI：`cli.*`, `__main__`, `bin/`, `cmd/`
   - 批处理/训练：`*train*`, `pipeline*`, `workflow*`
   - 前端：`src/main.*`, `index.html`, `app/`
5. **配置如何注入**：env / yaml / argparse / pydantic-settings / 硬编码（风险点）。
6. **外部依赖**：DB、缓存、MQ、对象存储、第三方 API、GPU、本地模型（Ollama 等）。

**大仓库策略**：按域拆分 Task 子 agent（如 `backend/`, `frontend/`, `ml/`, `infra/`），各返回 10 条以内要点，主 agent 合并。

### Phase 3：核心逻辑与数据流（10–20 分钟）

对**主路径**做「跟踪式阅读」——只跟一条 happy path：

1. 从入口到核心业务函数，画 **Mermaid 流程图**（请求链 / 训练链 / 事件链）。
2. 识别 **3–7 个关键模块**，每个模块说明：
   - 职责
   - 主要公开 API/类/函数
   - 上游/下游依赖
   - 复杂度与耦合风险
3. **数据生命周期**：从哪里来 → 如何变换 → 存哪里 → 如何读出。
4. **扩展点**：插件 hook、策略模式、feature flag、配置开关。
5. **已知复杂度热点**：大文件、循环依赖、上帝类、重复逻辑。

使用 `SemanticSearch` 提典型问题：

- "What is the main entry point and startup flow?"
- "How does authentication work?"
- "Where is the core business logic for X?"

### Phase 4：工程化与质量（5–10 分钟）

| 维度 | 检查项 |
|------|--------|
| 测试 | `test/`, `*_test.go`, `*.spec.*`；是否有 CI 跑测试；覆盖率声明 |
| 类型 | TypeScript strict、mypy、protobuf 等 |
| Lint/Format | eslint, ruff, black, prettier, pre-commit |
| CI/CD | GitHub Actions 触发条件、build/deploy 是否完整 |
| 安全 | 硬编码密钥、`.env` 提交、依赖漏洞面、SQL 拼接 |
| 文档 | API 文档、架构图、示例项目、与代码是否同步 |
| 可运维 | 日志、metrics、health check、graceful shutdown |
| 国际化/中文路径 | 路径含非 ASCII 时的已知坑 |

### Phase 5：运行验证（可选，用户要求或 Deep 模式）

1. 按 README 步骤安装依赖；记录**实际**命令与报错。
2. 最小可运行路径：help/version、单测子集、dry-run、docker compose config。
3. 结论三态：**已验证可运行** / **部分可运行（说明缺什么）** / **未验证（原因）**。
4. 不启动长期服务，除非用户明确要求；需要时用后台 shell 并验证 health。

### Phase 6：综合报告

使用 [report-template.md](report-template.md) 输出完整报告。

**Express 模式**可省略：详细 Mermaid、逐模块 API 列表、git 历史；保留 Executive Summary + 架构 + 优劣势 + 上手 3 步。

**Deep 模式额外**：

- `git log --oneline -20`、贡献者活跃度、最近 breaking change
- 依赖版本风险、TODO/FIXME 密度
- 与用户目标的匹配度评分（1–5）及理由

---

## 技术栈识别速查

详细 heuristics 见 [reference.md](reference.md)。默认规则：

- 多种清单并存时，以**实际入口语言**为准（有 `go.mod` 且 main 在 Go → Go 项目）。
- Monorepo：识别 workspace 工具（pnpm workspace, uv, nx, bazel）并分 package 说明。
- 生成式 AI 项目：额外标出 model provider、prompt 模板目录、RAG/vector store、agent 框架。

---

## 优劣势写法标准

**优势**：具体、可验证（例：「FastAPI + pydantic 校验完整」而非「代码不错」）。

**劣势/风险**：分等级

- 🔴 **阻塞**：缺依赖、无法运行、无许可证、明文密钥
- 🟡 **隐患**：测试弱、文档过期、强耦合、无 CI
- 🟢 **改进**：命名、结构优化、可观测性增强

**缺口清单**：仓库缺什么（validate 集、API 层、.env.example、一键脚本等）。

---

## 上手路径（报告必含）

固定输出 **15 分钟 / 1 小时 / 1 天** 三档：

1. **15 分钟**：读哪些文件、跑哪条命令、理解哪条主流程。
2. **1 小时**：改哪个小功能/跑哪组测试/跟完哪条 debug 链。
3. **1 天**：部署/扩展/贡献第一个 PR 的建议步骤。

---

## 反模式（禁止）

- ❌ 只复述 README 而不看代码
- ❌ 罗列目录树而不解释职责
- ❌ 未读入口就描述「架构」
- ❌ 把 dev 依赖写成 runtime 依赖
- ❌ 忽略 monorepo 子包边界
- ❌ 对没打开的文件声称「已实现」

---

## 附加资源

- 报告模板：[report-template.md](report-template.md)
- 文件优先级、栈识别、提问清单：[reference.md](reference.md)
