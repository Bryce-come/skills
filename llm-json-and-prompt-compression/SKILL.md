---
name: llm-json-and-prompt-compression
description: Compresses prompts and enforces strict JSON outputs for LLM calls (Azure OpenAI), including schema design, retries, timeout handling, and graceful fallback to non-LLM heuristics. Use when the user asks for "JSON输出", "结构化输出", "提示词太长", "空响应/截断", "重试/降级", or when 05_hybrid_prediction.py/LLM fusion is unstable.
---

# LLM JSON + Prompt Compression

## 目标

- **输出可解析的 JSON**（机器可用、可评测、可落盘）
- **缩短上下文**以降低超时/截断/空响应
- **失败可恢复**：重试、退避、降级（不让流程卡死）

## 1. JSON 输出设计

### 1.1 Schema 设计原则

1. 先定义 schema（字段名固定、类型固定、可选字段明确）
2. 约束输出：
   - 只输出 JSON
   - 不要 Markdown 代码块包裹
   - 不要多余解释

### 1.2 股票推荐场景 Schema

```json
{
  "trade_date": "YYYYMMDD",
  "market_view": {
    "sentiment": "risk-on|neutral|risk-off",
    "summary": "一句话结论",
    "key_signals": ["signal1", "signal2"]
  },
  "recommendations": [
    {
      "ts_code": "000001.SZ",
      "action": "buy|hold|avoid",
      "horizon": "1d|1w|1m",
      "confidence": 0.0,
      "reasons": ["原因1", "原因2"],
      "risk": ["风险1", "风险2"]
    }
  ],
  "errors": []
}
```

### 1.3 在 System Prompt 中强制 JSON

```
你是一个股票分析助手。你必须只输出合法的 JSON，不要输出任何其他内容。
不要使用 Markdown 代码块（不要 ```json）。
严格遵循以下 schema：{schema}
如果无法确定某字段，使用 null。
```

### 1.4 JSON 解析容错函数

```python
import json
import re

def parse_llm_json(raw: str) -> dict | None:
    """
    从 LLM 原始输出中提取 JSON：
    1. 先尝试直接 json.loads
    2. 失败则提取首个 { ... } 块再 parse
    3. 仍失败返回 None
    """
    # 尝试 1：直接解析
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass

    # 尝试 2：去掉 Markdown 代码块标记
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # 移除开头的 ```json 或 ```
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
        # 移除结尾的 ```
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)

    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        pass

    # 尝试 3：提取第一个完整的 { ... } 块
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, TypeError):
            pass

    return None
```

## 2. 提示词压缩策略（按优先级）

### 2.1 优先传"统计摘要"，不传整张表

**反面**：把 5000+ 行 `daily` CSV 直接塞 prompt
**正面**：只传统计指标

```python
def compress_daily_to_summary(daily: pd.DataFrame) -> str:
    """将全A股 daily 数据压缩为文本摘要（约 200 字）"""
    pct = daily['pct_chg']
    return f"""市场统计({daily.iloc[0]['trade_date']})：
- 股票数: {len(daily)}
- 上涨/下跌/平盘: {(pct>0).sum()}/{(pct<0).sum()}/{(pct==0).sum()}
- 涨跌幅: 均{pct.mean():.2f}%, 中位{pct.median():.2f}%
- 涨停(≥9.8%): {(pct>=9.8).sum()}, 跌停(≤-9.8%): {(pct<=-9.8).sum()}
- 成交额: {daily['amount'].sum()/1e8:.0f}亿, 前100只占比: {daily.nlargest(100,'amount')['amount'].sum()/daily['amount'].sum()*100:.1f}%
"""
```

### 2.2 Top-K 截断

- 只传板块 Top-5 / 个股 Top-25
- 不传所有板块/所有个股

```python
def compress_sector_stats(sector_stats: pd.DataFrame, top_k=5) -> str:
    """只保留 Top-K 和 Bottom-K 板块"""
    top = sector_stats.head(top_k)
    bottom = sector_stats.tail(top_k)
    return pd.concat([top, bottom]).to_string(index=True)
```

### 2.3 数值先聚合再传

- `groupby(industry)` 后只保留需要列与前后若干行
- 时间序列只传最近 5-10 个数据点

### 2.4 去噪

- 删除重复说明、长段落模板、冗余列
- 用 `df.to_string(index=False, max_rows=20)` 限制行数

### 2.5 压缩效果对比

| 原始大小 | 压缩后 | 方法 |
|---------|--------|------|
| daily 表 5000 行 (~500KB) | ~200 字 (~0.5KB) | 统计摘要 |
| 板块统计 80 行 | 10 行 | Top-5 + Bottom-5 |
| 25 只股票详情 | 25 行 | 每只 1 行关键指标 |

## 3. 重试与退避（稳态做法）

### 3.1 带退避的重试函数

```python
import time
import json

def call_llm_with_retry(
    client,
    deployment: str,
    messages: list[dict],
    max_retries: int = 3,
    max_tokens: int = 16384,
    expect_json: bool = True,
) -> str | dict | None:
    """
    带退避重试 + JSON 解析容错的 LLM 调用
    """
    backoff_times = [2, 5, 10]  # 秒

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=messages,
                max_completion_tokens=max_tokens,
            )
            raw = response.choices[0].message.content

            if not raw or not raw.strip():
                print(f"[警告] 第{attempt+1}次调用返回空内容")
                continue

            if expect_json:
                parsed = parse_llm_json(raw)
                if parsed is not None:
                    return parsed
                print(f"[警告] 第{attempt+1}次调用返回内容无法解析为 JSON，原始文本前100字: {raw[:100]}")
                # 在下一次重试时追加提示
                if attempt < max_retries - 1:
                    messages.append({"role": "assistant", "content": raw})
                    messages.append({"role": "user", "content": "上面的输出不是合法 JSON，请只输出纯 JSON，不要 Markdown 包裹。"})
                continue

            return raw

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                wait = backoff_times[min(attempt, len(backoff_times) - 1)]
                print(f"[重试] 限流，{wait}s 后重试 ({attempt+1}/{max_retries})...")
                time.sleep(wait)
            elif "timeout" in error_str.lower():
                print(f"[重试] 超时，缩短内容后重试 ({attempt+1}/{max_retries})...")
                # 截断最后一条 user message
                for msg in reversed(messages):
                    if msg["role"] == "user" and len(msg["content"]) > 500:
                        msg["content"] = msg["content"][:500] + "\n\n[内容已截断]"
                        break
            else:
                print(f"[错误] LLM 调用失败: {error_str}")
                if attempt == max_retries - 1:
                    return None

    return None
```

### 3.2 使用示例

```python
# 在 02_analysis.py 或 03_stock_prediction.py 中使用
result = call_llm_with_retry(
    client=client,
    deployment=deployment,
    messages=[
        {"role": "system", "content": "只输出纯 JSON。"},
        {"role": "user", "content": prompt},
    ],
    expect_json=True,
)
if result is None:
    # 走降级策略
    result = fallback_rule_based()
```

## 4. 降级策略（必须有）

当 LLM 失败时仍需输出结构化结果，不能让流程卡死：

```python
def fallback_rule_based(summary: pd.DataFrame, daily: pd.DataFrame, trade_date: str) -> dict:
    """LLM 失败时的规则降级方案"""
    pct = daily['pct_chg']
    up_ratio = (pct > 0).sum() / len(daily) if len(daily) > 0 else 0.5

    # 市场情绪由规则生成
    if up_ratio > 0.6:
        sentiment = "risk-on"
    elif up_ratio > 0.4:
        sentiment = "neutral"
    else:
        sentiment = "risk-off"

    # 推荐由本地评分生成（03_stock_prediction.py 的综合得分）
    top_stocks = daily.nlargest(10, 'pct_chg')[['ts_code', 'pct_chg']].to_dict('records')

    return {
        "trade_date": trade_date,
        "market_view": {
            "sentiment": sentiment,
            "summary": f"上涨占比{up_ratio:.1%}，{'偏多' if up_ratio > 0.5 else '偏空'}",
            "key_signals": [f"涨跌比{(pct>0).sum()}:{(pct<0).sum()}"]
        },
        "recommendations": [
            {"ts_code": s["ts_code"], "action": "hold", "confidence": 0.3,
             "reasons": ["涨幅靠前"], "risk": ["LLM 不可用，仅为规则推荐"]}
            for s in top_stocks
        ],
        "errors": ["LLM 调用失败，使用规则降级方案"]
    }
```

## 5. 项目中的应用位置

| 文件 | 当前状态 | 建议改进 |
|------|---------|---------|
| `02_analysis.py` | 直接 `client.chat.completions.create()` + 无重试 | 加 `call_llm_with_retry()` |
| `03_stock_prediction.py` | 同上 | 加重试 + 降级 |
| `05_hybrid_prediction.py` | LLM fusion | 确保 LLM 失败时退回到纯模型预测 |

## 6. 快速检查清单

- [ ] 所有 LLM 调用都有 try/except
- [ ] 至少 2 次重试 + 指数退避
- [ ] JSON 解析有容错（`parse_llm_json()`）
- [ ] LLM 失败时有降级输出（不是 `None` 或报错中断）
- [ ] prompt 中不传完整 daily 表（用压缩摘要代替）
- [ ] `errors` 字段记录所有降级/失败原因
