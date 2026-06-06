---
name: run-stock-agent
description: Runs the stock_agent workflow end-to-end or by steps (01-05), ensures .env is loaded, and validates that 02/03 use the same trade_date chosen by 01. Use when the user asks how to run, "跑通流程", "一键运行", "步骤01/02/03/04/05", or when outputs are out of sync across steps.
---

# Run Stock Agent

## 前置条件检查（必做）

运行前，先确认以下环境已就绪：

1. **Python 环境**：确保已安装 Python 3.10+
2. **依赖安装**：
   ```powershell
   pip install -r requirements.txt
   ```
3. **环境变量配置**：在项目根目录创建 `.env` 文件（参考 `env.example`）：
   ```ini
   TUSHARE_TOKEN=你的tushare_token
   AZURE_OPENAI_ENDPOINT=https://<resource>.cognitiveservices.azure.com/
   AZURE_OPENAI_API_KEY=你的api_key
   AZURE_OPENAI_DEPLOYMENT=gpt-5
   AZURE_OPENAI_API_VERSION=2024-12-01-preview
   ```
4. **验证 .env**：确保 `.env` 中无多余空格、key 未被引号包裹

## 工作流总览

```
01_data_fetch.py  →  02_analysis.py  →  03_stock_prediction.py
    (抓数据)            (AI分析)           (板块+个股推荐)
                                            ↓
                              04_lstm_gru_prediction_enhanced.py  (LSTM/GRU预测)
                                            ↓
                              05_hybrid_prediction.py  (混合预测, 需 --stock)
```

- 步骤 01 需要：`TUSHARE_TOKEN`
- 步骤 02 需要：`AZURE_OPENAI_*`
- 步骤 03 需要：`TUSHARE_TOKEN` + `AZURE_OPENAI_*`
- 步骤 04 需要：`TUSHARE_TOKEN`
- 步骤 05 需要：`TUSHARE_TOKEN` + `AZURE_OPENAI_*`

## Quick Start（默认推荐）

```powershell
# 进入项目目录
cd "E:\培训\Class14\智能体Stock"

# 一键运行 01+02+03（默认）
python -m stock_agent
```

## 常用命令

### 指定日期（只影响 01 抓数；02/03 以步骤01最终 trade_date 为准）
```powershell
python -m stock_agent --date 20260422
```

### 只跑部分步骤
```powershell
# 只抓数据
python -m stock_agent --steps 01

# 分析 + 推荐（前提：01 已跑过）
python -m stock_agent --steps 02,03

# 运行 LSTM/GRU 预测
python -m stock_agent --steps 04

# 运行混合预测（必须指定 --stock）
python -m stock_agent --steps 05 --stock 000001.SZ
```

### 指定模型类型（仅影响步骤04）
```powershell
python -m stock_agent --steps 04 --model-type gru
# 可选值：lstm（默认）、gru
```

### 直接运行单个脚本
```powershell
python 01_data_fetch.py --date 20260422
python 02_analysis.py --date 20260422
python 03_stock_prediction.py --date 20260422
python 04_lstm_gru_prediction_enhanced.py --mode 2 --model-type lstm
python 05_hybrid_prediction.py --stock 000001.SZ
```

## 一致性校验（关键机制）

项目约定：
- 步骤 01 会把最终使用的交易日写入：`a_share_out/_latest_trade_date.txt`
- 步骤 02/03 优先读取该文件（或由入口传 `--date`）以保证同一批数据贯穿全流程

**日期不一致排查**：
1. 确认 `a_share_out/_latest_trade_date.txt` 是否存在且内容为 8 位日期
2. 重新跑步骤 01：`python -m stock_agent --steps 01`
3. 再跑后续：`python -m stock_agent --steps 02,03`

## 输出文件说明

| 步骤 | 输出目录 | 文件名模式 |
|------|----------|-----------|
| 01 | `a_share_out/` | `daily_<date>.csv/.txt`, `index_<date>.csv/.txt`, `summary_<date>.csv/.txt`, `_latest_trade_date.txt` |
| 02 | `a_share_out/` | `analysis_<date>.txt` |
| 03 | `market_analysis/` | `market_sector_analysis_<date>.txt` |
| 04 | `lstm_models/`, `lstm_plots/`, `norm_params/`, `batch_predictions/` | 模型文件、图表、归一化参数 |
| 05 | `hybrid_predictions/` | 混合预测结果 |

## Windows 目录切换备忘

- **PowerShell**：
  ```powershell
  cd "E:\培训\Class14\智能体Stock"
  ```
- **cmd.exe**：
  ```cmd
  cd /d "E:\培训\Class14\智能体Stock"
  ```

## 常见失败与处理

| 故障现象 | 原因 | 解决方案 |
|---------|------|---------|
| `未找到 TUSHARE_TOKEN` | `.env` 缺少或未加载 | 确认 `.env` 在项目根目录，包含 `TUSHARE_TOKEN=` |
| `API调用失败` | Azure OpenAI 配置错误 | 参考 `troubleshoot-azure-openai` skill |
| 今天是交易日但 daily/index 为空 | Tushare 数据未更新 | 脚本会自动回退上一交易日；若未回退，参考 `troubleshoot-tushare-empty` skill |
| 步骤 02/03 用了老日期 | marker 文件过期 | 重新跑步骤 01 更新 marker |
| `步骤05需要指定 --stock 参数` | 05 必须指定股票代码 | 加 `--stock 000001.SZ` |

## 快速验证流程（从零开始）

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 .env（填写真实 token/key）
copy env.example .env
notepad .env

# 3. 一键运行
python -m stock_agent

# 4. 检查输出
dir a_share_out\
dir market_analysis\
```
