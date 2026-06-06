---
name: report-curation
description: Curates and summarizes generated outputs into a single human-friendly report, ensuring consistent trade_date and clear file links. Use when the user asks to "整理报告", "汇总输出", "生成 markdown 报告", or wants a single deliverable from a_share_out/ and market_analysis/.
---

# Report Curation

## 1. 输入（默认约定）

| 数据源 | 路径 | 内容 |
|--------|------|------|
| 市场情绪汇总 | `a_share_out/summary_<date>.csv` + `.txt` | 涨跌家数、成交额、涨跌停 |
| AI 市场分析 | `a_share_out/analysis_<date>.txt` | 8 维度深度分析 |
| 板块/个股报告 | `market_analysis/market_sector_analysis_<date>.txt` | Top-5 板块 + Top-25 热股 |
| 日期锚点 | `a_share_out/_latest_trade_date.txt` | 步骤 01 最终使用的交易日 |
| 指数数据 | `a_share_out/index_<date>.csv` | 三大指数行情 |

## 2. 一致性检查（必须先做）

生成报告前，确认所有文件日期一致：

```powershell
# 读取锚点日期
type a_share_out\_latest_trade_date.txt

# 检查所有文件是否存在且日期一致
dir a_share_out\*_20260425.*
dir market_analysis\*_20260425.*
```

**如不一致**：先修运行链路（重新跑 `python -m stock_agent --steps 01,02,03`），再汇总。

**用脚本验证**：
```python
import os, glob

def validate_date_consistency(base_dir: str = ".") -> str | None:
    """检查所有输出文件日期一致，返回一致的日期或 None"""
    marker = os.path.join(base_dir, "a_share_out", "_latest_trade_date.txt")
    if not os.path.exists(marker):
        print("[错误] 找不到 _latest_trade_date.txt")
        return None

    with open(marker, "r") as f:
        trade_date = f.read().strip()

    # 检查所有必需文件
    required = [
        f"a_share_out/summary_{trade_date}.csv",
        f"a_share_out/analysis_{trade_date}.txt",
        f"market_analysis/market_sector_analysis_{trade_date}.txt",
    ]
    for path in required:
        if not os.path.exists(os.path.join(base_dir, path)):
            print(f"[缺失] {path}")
            return None

    print(f"[通过] 所有文件日期一致: {trade_date}")
    return trade_date
```

## 3. 报告生成

### 3.1 手动生成（推荐）

运行以下 Python 脚本一键生成汇总报告：

```python
#!/usr/bin/env python3
"""report_curation.py - 汇总生成单页 Markdown 报告"""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "a_share_out")
MARKET_DIR = os.path.join(BASE_DIR, "market_analysis")

def get_trade_date() -> str:
    marker = os.path.join(OUT_DIR, "_latest_trade_date.txt")
    with open(marker, "r", encoding="utf-8") as f:
        return f.read().strip()

def read_section(path: str, label: str) -> str:
    if not os.path.exists(path):
        return f"**{label}**: 文件不存在\n\n"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # 截取 AI 分析部分（跳过文件头部的数据表）
    if "AI" in content or "分析" in content:
        # 找到 AI 分析部分的起始位置
        for keyword in ["AI分析结果", "AI深度分析结果", "分析结果"]:
            idx = content.find(keyword)
            if idx >= 0:
                content = content[idx:]
                break
    return content

def generate_report() -> str:
    trade_date = get_trade_date()

    # 读取 summary
    summary_path = os.path.join(OUT_DIR, f"summary_{trade_date}.csv")
    summary = pd.read_csv(summary_path) if os.path.exists(summary_path) else None

    # 读取 index
    index_path = os.path.join(OUT_DIR, f"index_{trade_date}.csv")
    index_df = pd.read_csv(index_path) if os.path.exists(index_path) else None

    # 读取分析报告
    analysis = read_section(os.path.join(OUT_DIR, f"analysis_{trade_date}.txt"), "市场分析")

    # 读取板块报告
    sector = read_section(os.path.join(MARKET_DIR, f"market_sector_analysis_{trade_date}.txt"), "板块分析")

    # 构建 Markdown 报告
    report = f"""# A股市场日报 - {trade_date}

## 一、市场概览

"""
    if summary is not None and not summary.empty:
        s = summary.iloc[0]
        report += f"""- 交易日: **{trade_date}**
- 股票总数: {int(s['stocks'])}
- 上涨: {int(s['up'])} / 下跌: {int(s['down'])} / 平盘: {int(s['flat'])}
- 总成交额: {s['amt_total_yi_est']:.0f} 亿元
- 涨停: {int(s['limit_up_10_est'] + s['limit_up_20_est'])} / 跌停: {int(s['limit_dn_10_est'] + s['limit_dn_20_est'])}

"""

    if index_df is not None and not index_df.empty:
        report += "### 三大指数\n\n"
        name_map = {"000001.SH": "上证指数", "399001.SZ": "深证成指", "399006.SZ": "创业板指"}
        for _, row in index_df.iterrows():
            name = name_map.get(row['ts_code'], row['ts_code'])
            report += f"- **{name}**: {row['close']:.2f} ({row['pct_chg']:+.2f}%), 成交额 {row['amount']/1e8:.0f}亿\n"
        report += "\n"

    report += f"""## 二、AI 市场分析

{analysis}

## 三、热门板块与个股

{sector}

---

> 报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
> 数据来源: Tushare + Azure OpenAI
> **免责声明**: 本报告仅供学习参考，不构成任何投资建议。
"""

    return report

if __name__ == "__main__":
    report = generate_report()
    trade_date = get_trade_date()
    output_path = os.path.join(BASE_DIR, f"report_{trade_date}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[完成] 报告已生成: {output_path}")
```

### 3.2 一键运行

```powershell
cd "E:\培训\Class14\智能体Stock"
python report_curation.py
```

生成的报告文件：`report_<date>.md`（项目根目录）

### 3.3 报告模板结构

```markdown
# A股市场日报 - YYYYMMDD

## 一、市场概览
- 交易日 / 涨跌家数 / 成交额 / 涨跌停

### 三大指数
- 上证 / 深证 / 创业板 涨跌幅 + 成交额

## 二、AI 市场分析
- 8 维度分析摘要（指数原因、结构、资金、技术面、情绪、风险、策略、次日信号）

## 三、热门板块与个股
- Top-5 板块 + 每板块 Top-5 股票（共 25 只）
- 各维度评分 + 技术指标

---
> 免责声明
```

## 4. 自定义报告内容

### 只看市场概览
```python
# 只输出 summary + index，不包含 AI 分析
report = generate_report()
sections = report.split("## 二、AI 市场分析")
brief_report = sections[0] + "\n---\n> 免责声明: 仅供学习参考"
```

### 只看板块个股
```python
# 只输出板块分析
report = generate_report()
sections = report.split("## 三、热门板块与个股")
sector_report = "# 板块与个股分析\n\n" + sections[1] if len(sections) > 1 else "无数据"
```

## 5. 常见问题

**Q: `analysis_<date>.txt` 内容太长怎么办？**
A: 报告脚本会自动定位 AI 分析部分，跳过头部的数据表。如果仍太长，可截取前 2000 字。

**Q: 没有 AI 分析报告（步骤 02 未跑）？**
A: 报告会显示"文件不存在"，其余部分正常生成。建议先跑 `python -m stock_agent --steps 02`。

**Q: 日期不一致？**
A: 重新运行完整流程：`python -m stock_agent`（会自动跑 01+02+03，保证日期一致）。
