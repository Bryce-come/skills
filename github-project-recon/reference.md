# 项目快读参考手册

本文件供 Phase 1–4 深度侦察时按需阅读，不必一次全读。

---

## 1. 文件阅读优先级

### P0 — 必读（存在就读）

| 文件模式 | 获取信息 |
|----------|----------|
| `README*` | 目标、安装、用法 |
| `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` | 依赖、脚本、版本 |
| `docker-compose*.yml` / `Dockerfile*` | 运行时拓扑 |
| `.github/workflows/*` | CI 做什么 |
| 主入口（见 §2） | 启动链 |

### P1 — 架构理解

| 文件模式 | 获取信息 |
|----------|----------|
| `docs/**/*.md`, `mkdocs.yml`, `docusaurus` | 深度文档 |
| `ARCHITECTURE*`, `DESIGN*` | 设计意图 |
| `src/**/main.*`, `app/**`, `internal/**` | 模块边界 |
| `openapi*.yaml`, `swagger*`, `routes/` | API 面 |
| `migrations/`, `alembic/`, `schema/` | 数据模型 |
| `Makefile`, `justfile`, `Taskfile` | 常用命令 |

### P2 — 质量与运维

| 文件模式 | 获取信息 |
|----------|----------|
| `test/**`, `*_test.*`, `*.spec.*` | 测试习惯 |
| `.pre-commit-config.yaml` | 提交门禁 |
| `helm/`, `k8s/`, `terraform/` | 部署 |
| `logging.conf`, `prometheus`, `grafana` | 可观测性 |

### P3 — 按需

| 文件模式 | 获取信息 |
|----------|----------|
| `examples/`, `samples/` | 用法示例 |
| `benchmarks/` | 性能取向 |
| `scripts/` | 运维/数据脚本 |
| `notebooks/` | 探索性 ML |

---

## 2. 入口点 Heuristics

### Python

```bash
# 常见入口
rg -l "if __name__ == .__main__." --glob "*.py"
rg -l "FastAPI|Flask|Django|uvicorn|gunicorn" --glob "*.py"
rg -l "typer|click|argparse" --glob "*.py"
```

关注：`app.py`, `main.py`, `manage.py`, `wsgi.py`, `asgi.py`, `cli.py`, `start_*.py`

### Node / Frontend

- `package.json` → `scripts.start`, `main`, `bin`
- `src/index.ts`, `src/main.tsx`, `app/page.tsx` (Next.js)
- `vite.config.*`, `next.config.*`, `nuxt.config.*`

### Go

- `cmd/*/main.go`
- `go.mod` module path

### Rust

- `src/main.rs` (binary) vs `src/lib.rs` (library)
- `Cargo.toml` `[[bin]]`

### Java / Kotlin

- `Application.java`, `@SpringBootApplication`
- `build.gradle` → `mainClass`

### 通用

- `docker-compose` 的 `command` / `entrypoint`
- `Procfile`, `supervisord.conf`
- GitHub Actions 里的 `run:` 命令

---

## 3. 架构模式识别

| 信号 | 可能架构 |
|------|----------|
| `controllers/` + `services/` + `repositories/` | 分层 MVC/DDD |
| `domain/`, `application/`, `infrastructure/` | Clean/Hexagonal |
| `packages/*`, `apps/*`, `pnpm-workspace` | Monorepo 多应用 |
| `worker/`, `celery`, `rq`, `sidekiq` | 异步任务 |
| `pipelines/`, `dags/`, `airflow` | 批处理编排 |
| `agents/`, `tools/`, `chains/` | LLM Agent |
| `embeddings/`, `vector`, `rag/` | RAG 系统 |
| 仅 `lib/` + 无 server | SDK/Library |
| `cmd/` + 单模块 | Go CLI 工具 |

---

## 4. 技术栈指纹

| 文件 | 栈 |
|------|-----|
| `requirements.txt` + `FastAPI` | Python API |
| `poetry.lock` / `uv.lock` | 现代 Python 打包 |
| `environment.yml` | Conda |
| `setup.py` + `torch` | ML 训练 |
| `package-lock.json` + `react` | React SPA |
| `pnpm-lock.yaml` + `next` | Next.js |
| `go.sum` | Go |
| `Gemfile` + `rails` | Ruby on Rails |
| `composer.json` | PHP |
| `mix.exs` | Elixir |
| `BUILD.bazel` | Bazel monorepo |

---

## 5. SemanticSearch 提问库

按项目类型选用 5–8 个：

**通用**
- How does the application start and what is the main entry point?
- Where is configuration loaded and validated?
- How are errors handled and logged?

**Web/API**
- How are routes defined and middleware applied?
- How does authentication and authorization work?
- Where is the database accessed?

**ML/Data**
- What is the training pipeline from raw data to model artifact?
- Where are features engineered and datasets split?
- How is inference served or exported?

**Frontend**
- How is state managed and how do pages fetch data?
- What is the routing structure?

**Infra**
- How is the project deployed and what services does it depend on?

---

## 6. Grep 快速侦察命令

在项目根执行（agent 用 Grep 工具等价实现）：

```bash
# 体量与语言
# （由 scan_project.py 完成）

# 敏感信息粗扫
rg -i "password\s*=|api_key\s*=|secret\s*=|AKIA[0-9A-Z]{16}" --glob "!*.lock" --glob "!node_modules"

# 未完成功能
rg "TODO|FIXME|HACK|XXX" --count-matches | head -30

# 对外 API 面
rg "@app\.(get|post|put|delete)|router\.(get|post)|@Route" --glob "*.py" --glob "*.ts" -l

# 环境变量引用
rg "os\.getenv|os\.environ|process\.env|env\." --glob "!node_modules" -l | head -20
```

---

## 7. Git 历史（Deep 模式）

```bash
git log --oneline -20
git log --since="6 months ago" --oneline | wc -l
git shortlog -sn --since="1 year ago" | head -10
git tag -l | tail -5
```

解读：
- 6 个月无提交 → 维护停滞风险
- 单贡献者 → 巴士因子低
- 最近大量 `fix`/`revert` → 稳定性存疑

---

## 8. 成熟度评分 Rubric（1–5）

| 分数 | 文档 | 测试 | 可运行 | CI |
|------|------|------|--------|-----|
| 5 | 架构+API+示例齐全 | 覆盖核心路径+CI | 一键启动 | build+test+deploy |
| 4 | README 完整 | 有集成测试 | 文档步骤可跑 | build+test |
| 3 | README 基本可用 | 少量单测 | 需改配置才能跑 | 仅 lint |
| 2 | 仅标题 | 几乎无 | 缺依赖/数据 | 无 |
| 1 | 无/过期 | 无 | 无法跑 | 无 |

---

## 9. 常见「GitHub 下载项目」陷阱

| 现象 | 含义 |
|------|------|
| 有 `docker-compose` 无 `.env.example` | 环境变量靠猜 |
| README 路径与仓库不一致 | 文档未同步 |
| 大 CSV/模型在 repo 外 | 需额外下载 |
| `models/` 空目录 | 需先训练 |
| 中文路径 + joblib/pickle | Windows 写入可能失败 |
| `requirements.txt` 无版本上限 | 环境不可复现 |
| 示例脚本引用不存在文件 | 半成品 |

---

## 10. Monorepo 阅读策略

1. 读 workspace 根清单（`pnpm-workspace.yaml`, `go.work`, `Cargo.toml` workspace）
2. 每个 package 单独找 README + 入口
3. 画依赖图：谁依赖谁（内部 packages）
4. 分别标「可独立运行」与「仅 library」

---

## 11. 输出语言与格式

- 默认中文；保留英文专有名词（FastAPI, Redis）
- 路径用反引号；代码引用用 `startLine:endLine:path` 格式
- Mermaid 用于主流程；超过 15 节点则拆图
- 表格优于长段落枚举

---

## 12. 与用户目标对齐（可选章节）

若用户说明目的，在报告末尾加：

| 用户目标 | 匹配度(1–5) | 理由 |
|----------|-------------|------|
| 学习参考 | | |
| 生产接入 | | |
| 二次开发 | | |
| 课程作业 | | |
