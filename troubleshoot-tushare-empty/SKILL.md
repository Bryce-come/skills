---
name: troubleshoot-tushare-empty
description: Diagnoses Tushare returning empty daily/index data, including "today is trading day but data empty", permission/points issues, and automatic fallback to previous trade dates. Use when the user sees empty CSVs, summary shows 0 stocks, or Tushare warns about permissions/积分.
---

# Troubleshoot Tushare Empty Data

## 1. 快速诊断（最常见原因）

| 现象 | 最可能原因 | 严重程度 |
|------|-----------|---------|
| 今天的 daily/index 返回空 | Tushare 当日数据尚未更新（收盘后 2-4 小时更新） | 正常，自动回退即可 |
| 任何历史日期都返回空 | `TUSHARE_TOKEN` 为空、过期或积分不足 | 需修复 |
| 只有部分接口为空 | 权限分级：`daily` 免费，`daily_basic`/`stock_basic` 需积分 | 部分 API 受限 |
| 脚本直接报 `权限` 或 `积分` 错误 | 积分不够 | 需升级账户 |

## 2. 自动回退机制说明

`01_data_fetch.py` 已内置自动回退逻辑：
1. 先查询交易日历，找到目标日期最近的开市日
2. 如果该日期的 `daily` 数据为空，自动尝试前一个交易日
3. 最多回退 3 次
4. 回退成功后写入 `a_share_out/_latest_trade_date.txt`

**确认回退是否生效**：
```powershell
# 查看最终使用的交易日
type a_share_out\_latest_trade_date.txt
```

## 3. 手动处理步骤（按优先级）

### 步骤 1：尝试运行 01（让自动回退生效）
```powershell
cd "E:\培训\Class14\智能体Stock"
python -m stock_agent --steps 01
```

确认控制台出现类似：
```
[提示] 20260426 数据未就绪或为空，自动回退到上一个交易日 20260425 重试。
```

确认 `_latest_trade_date.txt` 已更新：
```powershell
type a_share_out\_latest_trade_date.txt
```

### 步骤 2：验证数据落盘是否真实
```powershell
# 检查 daily CSV 行数
python -c "import pandas as pd; df = pd.read_csv('a_share_out/daily_<date>.csv'); print(f'行数: {len(df)}')"

# 检查 summary 中 stocks 字段
python -c "import pandas as pd; df = pd.read_csv('a_share_out/summary_<date>.csv'); print(f'stocks: {df.iloc[0][\"stocks\"]}')"
```

- `daily_<date>.csv` 行数 > 0 → 数据正常
- `summary_<date>.csv` 中 `stocks > 0` → 数据正常

### 步骤 3：排除 Token / 权限问题

**验证 Token 是否有效**：
```powershell
python -c "
from dotenv import load_dotenv; import os
load_dotenv()
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print('TUSHARE_TOKEN 未设置！')
else:
    print(f'Token 长度: {len(token)}, 前4位: {token[:4]}...')
    import tushare as ts
    pro = ts.pro_api(token)
    try:
        df = pro.daily(trade_date='20260102', fields='ts_code', limit=1)
        print(f'接口测试: 返回 {len(df)} 行')
    except Exception as e:
        print(f'接口测试失败: {e}')
"
```

**Token 常见问题**：
- `.env` 中 `TUSHARE_TOKEN=` 后面有空格 → 删除空格
- Token 被引号包裹 → 删除引号
- Token 过期 → 到 [Tushare 官网](https://tushare.pro/) 重新获取
- 积分不足 → 升级账户或完成社区任务获取积分

### 步骤 4：换日期重试
```powershell
# 指定一个确定有数据的历史交易日
python -m stock_agent --steps 01 --date 20260102
```

若指定历史日期仍为空 → 确认是 Token/权限问题，不是数据延迟

## 4. 输出对齐（防止 02/03 用错日期）

一旦步骤 01 回退成功，后续步骤使用 marker 中的日期：

```powershell
# 步骤 01 成功后
python -m stock_agent --steps 02,03
```

**验证日期一致性**：
```powershell
# 所有输出文件的日期应该一致
dir a_share_out\*_20260425.*
dir market_analysis\*_20260425.*
```

## 5. Tushare 接口权限速查

| 接口 | 所需积分 | 本项目用途 |
|------|---------|-----------|
| `daily` | 0（免费） | 日行情数据 |
| `index_daily` | 0（免费） | 指数行情 |
| `trade_cal` | 0（免费） | 交易日历 |
| `stock_basic` | ≥120 | 股票基本信息（行业分类） |
| `daily_basic` | ≥2000 | 每日基本面（换手率、PE 等） |

如果 `stock_basic` 或 `daily_basic` 返回空，说明积分不足。项目代码已有降级处理（使用估算值），不会导致流程中断，但分析精度会降低。

## 6. 常见问题 Q&A

**Q: 盘中运行 01 显示数据为空？**
A: 正常。Tushare 盘中不更新日线数据，需等到收盘后 2-4 小时。脚本会自动回退到上一个交易日。

**Q: 周末/节假日运行？**
A: 脚本会自动回退到最近的交易日，无需手动指定日期。

**Q: 自动回退后 summary 显示 stocks=0？**
A: 回退到的日期可能也没有数据（极罕见）。尝试手动指定更早的日期：
```powershell
python -m stock_agent --steps 01 --date 20260301
```

**Q: `daily_basic` 接口报权限错误但不影响主流程？**
A: 正常。`daily_basic` 需要较高积分。代码已有降级逻辑：缺少换手率数据时会使用估算值。
