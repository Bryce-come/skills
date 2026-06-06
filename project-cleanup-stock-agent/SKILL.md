---
name: project-cleanup-stock-agent
description: Cleans and standardizes the Stock Agent project by removing unrelated scripts, caches, and sensitive files, and by keeping env.example/README/requirements aligned. Use when the user asks to "清理无用文件", "规范目录", "准备交付/分享", or wants a minimal reproducible project.
---

# Project Cleanup (Stock Agent)

## 1. 清理目标

将项目精简到最小可复现集合，去除缓存、临时输出、敏感文件，使其适合分享/交付/Git 提交。

## 2. 安全与可分享性

### 2.1 敏感文件处理

| 文件 | 处理方式 | 说明 |
|------|---------|------|
| `.env` | **绝不提交** | 包含 TUSHARE_TOKEN 和 AZURE_OPENAI_API_KEY |
| `env.example` | **保留** | 模板文件，不含真实密钥 |
| `.gitignore` | **确保包含 `.env`** | 防止误提交敏感信息 |

### 2.2 代码硬编码检查

```powershell
# 搜索代码中是否有硬编码的 key/token
findstr /s /i "api.key.*=" *.py
findstr /s /i "token.*=" *.py
findstr /s /i "password" *.py
# 确保所有密钥只从 os.getenv() 读取
```

## 3. 可删除内容

### 3.1 Python 缓存（安全删除）

```powershell
# 删除所有 __pycache__ 目录
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# 删除 .pyc/.pyo 文件
Get-ChildItem -Path . -Recurse -File -Include "*.pyc","*.pyo" | Remove-Item -Force
```

### 3.2 运行产生的临时输出（可选删除）

如果只需分享代码（不含数据）：

```powershell
# 删除 a_share_out 中的数据文件（保留 .gitkeep）
Get-ChildItem -Path a_share_out -File | Where-Object { $_.Name -ne ".gitkeep" } | Remove-Item -Force

# 删除 market_analysis 中的数据文件
Get-ChildItem -Path market_analysis -File | Where-Object { $_.Name -ne ".gitkeep" } | Remove-Item -Force

# 删除模型和预测输出
Remove-Item -Path lstm_models -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path lstm_plots -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path norm_params -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path batch_predictions -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path hybrid_predictions -Recurse -Force -ErrorAction SilentlyContinue
```

### 3.3 一键清理脚本

```powershell
# 完整清理（缓存 + 输出数据，保留源码和 .gitkeep）
cd "E:\培训\Class14\智能体Stock"

# 1. 清理 Python 缓存
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# 2. 清理输出数据
@("a_share_out","market_analysis") | ForEach-Object {
    Get-ChildItem -Path $_ -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne ".gitkeep" } |
        Remove-Item -Force
}

@("lstm_models","lstm_plots","norm_params","batch_predictions","hybrid_predictions") | ForEach-Object {
    Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "[完成] 清理完毕"
```

### 3.4 重新创建必要的空目录

```powershell
# 确保输出目录存在（含 .gitkeep）
@("a_share_out","market_analysis","lstm_models","lstm_plots","norm_params","batch_predictions") | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
    New-Item -ItemType File -Path "$_/.gitkeep" -Force | Out-Null
}
```

## 4. 保留的最小可复现集合

### 4.1 必须保留

```
智能体Stock/
├── stock_agent/
│   ├── __init__.py
│   ├── __main__.py
│   └── cli.py
├── 01_data_fetch.py
├── 02_analysis.py
├── 03_stock_prediction.py
├── 04_lstm_gru_prediction_enhanced.py
├── 05_hybrid_prediction.py
├── requirements.txt
├── .env                    # 本地使用，不提交
├── env.example             # 提交
├── .gitignore
└── README.md
```

### 4.2 可选保留

| 文件 | 说明 |
|------|------|
| `ENHANCEMENT_GUIDE.md` | 增强指南 |
| `INVESTMENT_ADVICE_GUIDE.md` | 投资建议指南 |
| `MODEL_IMPROVEMENT_GUIDE.md` | 模型改进指南 |
| `LOW_ACCURACY_HANDLING.md` | 低精度处理指南 |
| `.cursor/skills/` | Agent Skills 配置 |

### 4.3 不应保留

| 文件/目录 | 原因 |
|----------|------|
| `__pycache__/` | 编译缓存 |
| `*.pyc` | 编译产物 |
| `a_share_out/*.csv` | 运行时数据 |
| `a_share_out/*.txt` | 运行时输出 |
| `lstm_models/` 内的文件 | 训练产物 |
| `lstm_plots/` 内的图片 | 可重新生成 |

## 5. .gitignore 检查清单

确认 `.gitignore` 包含以下内容：

```gitignore
# 敏感配置
.env

# Python 缓存
__pycache__/
*.py[cod]
*$py.class
*.so

# 运行输出
a_share_out/*
!a_share_out/.gitkeep
market_analysis/*
!market_analysis/.gitkeep
lstm_models/
lstm_plots/
norm_params/
batch_predictions/
hybrid_predictions/

# IDE
.vscode/
.idea/

# 系统文件
.DS_Store
Thumbs.db
```

**验证 .gitignore 是否生效**：
```powershell
git status
# 确认 .env、a_share_out/ 下的数据文件未被跟踪
```

## 6. 交付前最终检查

```powershell
# 1. 确认 .env 不在 Git 跟踪中
git ls-files | Select-String ".env"
# 如果出现 .env，执行：git rm --cached .env

# 2. 确认无硬编码密钥
findstr /s /r "sk-[a-zA-Z0-9]\{20,\}" *.py
findstr /s /r "[a-f0-9]\{32\}" *.py

# 3. 确认依赖完整
pip install -r requirements.txt
python -m stock_agent --steps 01 --date 20260102

# 4. 确认 .gitignore 生效
git add -A
git status
```

## 7. 快速操作汇总

| 目标 | 命令 |
|------|------|
| 清理缓存 | `Get-ChildItem -Recurse -Directory -Filter "__pycache__" \| Remove-Item -Recurse -Force` |
| 清理输出数据 | 见 3.3 一键清理脚本 |
| 验证 .gitignore | `git status` |
| 从零验证项目 | `pip install -r requirements.txt && python -m stock_agent --steps 01` |
| 准备交付 | 清理缓存 + 清理数据 + 验证 .gitignore + `git add -A && git status` |
