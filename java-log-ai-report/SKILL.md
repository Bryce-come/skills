---
name: java-log-ai-report
description: >-
  Fixes the Zhipu AI output template for week19 Java log analysis reports.
  Use when editing reporter.py, ai_template.py, AI prompts, or when the user
  asks to standardize, fix, or customize the §6 AI analysis section format.
---

# Java 日志 AI 报告模板 Skill

## 何时使用

- 修改 `week19/reporter.py` 中的 AI prompt 或 system message
- 用户要求固定 / 调整 AI 分析输出格式
- AI 输出结构不稳定（缺章节、有开场白、格式混乱）

## 单一事实来源

| 文件 | 职责 |
|------|------|
| [template.md](template.md) | 人类可读的完整模板规范 |
| [ai_template.py](../../ai_template.py) | 代码中的 SYSTEM_PROMPT / OUTPUT_FORMAT / 校验 |
| [reporter.py](../../reporter.py) | `_build_ai_prompt()` 引用 `ai_template` |

**改模板时同步更新三处**，以 `template.md` 为设计基准。

## 固定输出结构（§6）

AI 只负责生成报告第 6 章，必须包含：

```
### 6.1 执行摘要
### 6.2 根因推测
### 6.3 优先级建议
  #### P0 - 紧急
  #### P1 - 高
  #### P2 - 中
  #### P3 - 低
### 6.4 时间线概览
### 6.5 运维建议
```

§1~§5（统计表格 + matplotlib 图表）由 Python 代码生成，**AI 不得重复输出**。

## 修改流程

1. 编辑 [template.md](template.md) 调整章节设计
2. 同步 [ai_template.py](../../ai_template.py) 中的 `SYSTEM_PROMPT`、`OUTPUT_FORMAT`、`REQUIRED_HEADINGS`
3. 确认 [reporter.py](../../reporter.py) 的 `_build_ai_prompt()` 调用：
   - `from ai_template import SYSTEM_PROMPT, build_format_instruction`
   - system message 使用 `SYSTEM_PROMPT`
   - user prompt 末尾追加 `build_format_instruction()`
4. 运行验证：
   ```bash
   cd week19
   python main.py --input train.csv --output output/report.md --skip-ai  # 快速测图表
   python main.py --input train.csv --output output/report.md            # 完整测 AI 模板
   ```
5. 检查 `output/report.md` §6 是否包含全部必需标题

## 校验

```python
from ai_template import validate_ai_output

missing = validate_ai_output(ai_text)
if missing:
    print("缺失章节:", missing)
```

`reporter.py` 在 API 返回后可调用 `validate_ai_output`；有缺失时在控制台打印警告（不阻断写入）。

## 禁止事项

- AI 输出「你好」「我是专家」等开场白
- 自定义 §6 以外的章节编号
- 在 AI 输出中重复 §1~§5 统计表
- 省略 P0~P3 任一优先级小节（无内容写「暂无」）

## 示例片段

合格的 §6 开头：

```markdown
### 6.1 执行摘要

系统在 14:00~15:00 出现 22 条错误，错误率 44.9%，以数据库连接与 Redis 连接池耗尽为主，需紧急介入。

### 6.2 根因推测

**核心结论**：高并发下基础设施资源枯竭引发级联故障。

| 关联错误类型 | 关联说明 |
|--------------|----------|
| `DB_CONNECTION_ERROR` + `REDIS_POOL_EXHAUSTED` | 连接池耗尽导致业务层大面积超时 |
```

不合格（有开场白、缺固定标题）：

```markdown
你好！我是 Java 应用日志分析专家。以下是我的分析：

### 1. 根因推测
...
```

## 延伸阅读

- 完整模板：[template.md](template.md)
- 项目文档：[README.md](../../README.md) §8 报告输出结构
