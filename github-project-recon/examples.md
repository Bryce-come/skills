# 使用示例

## 示例 1：Express 快读

**用户**：帮我快速看一下 `@some-repo/` 是做什么的，值不值得用。

**Agent 应**：
1. 读取 `github-project-recon` skill
2. 运行 `python scripts/scan_project.py "some-repo"`
3. 读 README + 主 manifest + 入口文件
4. 输出 Express 报告（Summary + 栈 + 优劣势 + 15 分钟上手）

---

## 示例 2：Standard 接手项目

**用户**：我刚 clone 了这个项目，帮我通读了解架构和代码逻辑。

**Agent 应**：
1. Standard 模式
2. Phase 0–4 全做
3. 画 Mermaid 主流程
4. 列出 P0/P1 阅读清单
5. 附 SWOT 与缺口清单

---

## 示例 3：Deep + 能否运行

**用户**：分析这个 GitHub 项目，并验证能不能跑起来。

**Agent 应**：
1. Deep 模式 + Phase 5
2. 按 README 安装依赖并试跑
3. 运行结果三态写进报告
4. git log 摘要

---

## 示例 4：Monorepo

**用户**：这是个 monorepo，帮我搞清楚每个子项目是干什么的。

**Agent 应**：
1. 识别 workspace 配置
2. 每个 package 单独一行：名称 / 入口 / 可否独立运行
3. 画 package 依赖关系图

---

## 示例 5：ML 项目

**用户**：快速读懂这个训练仓库。

**Agent 应额外关注**：
- 数据在哪、模型 artifact 路径
- train / eval / infer 脚本
- 缺 validate 集或预训练权重时的影响
- GPU/外部 API 依赖

---

## 触发词参考

用户可能说：
- 快速阅读 / 通读 / 扫一眼 / 项目调研
- 了解新项目 / 架构梳理 / 代码结构分析
- GitHub 下载的项目 / clone 下来的仓库
- onboarding / recon / 技术选型

以上均应激活本 skill。
