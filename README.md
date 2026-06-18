# 个人 Skills 索引

路径：`C:\Users\Administrator\.cursor\skills\`

此处为**个人级 Skill**，对本机所有 Cursor 项目可用。在对话中 @ skill 名称或描述触发场景即可使用。

---

## 已安装（10 个）

| Skill | 来源 | 用途摘要 |
|-------|------|----------|
| [github-project-recon](./github-project-recon/) | 本机新建 | 快速通读 GitHub/本地项目：架构、逻辑、优劣势、上手路径 |
| [run-stock-agent](./run-stock-agent/) | Class14 智能体Stock | 股票 Agent 01–05 全流程运行与 trade_date 同步 |
| [troubleshoot-azure-openai](./troubleshoot-azure-openai/) | Class14 智能体Stock | Azure OpenAI 调用失败诊断与修复 |
| [troubleshoot-tushare-empty](./troubleshoot-tushare-empty/) | Class14 智能体Stock | Tushare 空数据、权限、回退交易日 |
| [llm-json-and-prompt-compression](./llm-json-and-prompt-compression/) | Class14 智能体Stock | LLM 结构化 JSON 输出、提示词压缩、重试降级 |
| [report-curation](./report-curation/) | Class14 智能体Stock | 汇总 a_share_out / market_analysis 为交付报告 |
| [project-cleanup-stock-agent](./project-cleanup-stock-agent/) | Class14 智能体Stock | 清理 Stock 项目、规范目录、准备交付 |
| [web-access](./web-access/) | Class14 智能体Stock | 联网搜索、网页抓取、浏览器自动化（含 scripts） |
| [stop-slop-main](./stop-slop-main/) | 第三方 | 去除 AI 写作痕迹，润色与审校 prose |
| [java-log-ai-report](./java-log-ai-report/) | 项目/1ai-log-analysis | Java 日志 AI 报告 §6 模板与 prompt 规范 |

---

## Cursor 内置 Skills（勿复制到此目录）

以下位于 `C:\Users\Administrator\.cursor\skills-cursor\`，由 Cursor 自动管理，**无需也不应**复制到 `skills\`：

| 内置 Skill | 用途 |
|------------|------|
| create-skill | 编写新 Skill |
| create-rule | 编写 Cursor Rules |
| create-hook | 编写 Hooks |
| canvas | 生成 Canvas 可视化产物 |
| babysit | PR 评论与 CI 循环修复 |
| split-to-prs | 拆分 PR |
| sdk | Cursor SDK 集成 |
| loop | 定时/循环任务 |
| shell | 终端命令执行 |
| statusline | CLI 状态栏配置 |
| update-cursor-settings | 修改 settings.json |
| update-cli-config | CLI 配置 |
| migrate-to-skills | 迁移到 Skills 体系 |

---

## 项目级 Skills（仍保留在原仓库）

`e:\培训\Class14\智能体Stock\.cursor\skills\` 中的 7 个 Skill **已复制**到本目录；原项目内副本仍保留，便于随仓库分享。

其他 Class 目录暂无 `.cursor/skills/`。

---

## 新增 Skill

```text
C:\Users\Administrator\.cursor\skills\<skill-name>\SKILL.md
```

命名：小写 + 连字符，见 `create-skill` 内置规范。
