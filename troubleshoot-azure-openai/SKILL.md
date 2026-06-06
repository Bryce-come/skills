---
name: troubleshoot-azure-openai
description: Diagnoses Azure OpenAI failures (auth, deployment not found, quota, timeout, empty responses) and applies safe mitigations (env checks, smaller prompts, retries, JSON enforcement). Use when 02_analysis.py or 03_stock_prediction.py prints API调用失败 or returns empty analysis.
---

# Troubleshoot Azure OpenAI

## 1. 环境检查（必做第一步）

确认 `.env` 或系统环境变量存在且格式正确：

| 变量名 | 示例值 | 检查要点 |
|--------|--------|---------|
| `AZURE_OPENAI_ENDPOINT` | `https://myresource.cognitiveservices.azure.com/` | 必须以 `https://` 开头，以 `/` 结尾 |
| `AZURE_OPENAI_API_KEY` | `abc123...` | 32 位十六进制字符串，无空格 |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-5` | **必须与 Azure Portal 中的部署名一致**（区分大小写） |
| `AZURE_OPENAI_API_VERSION` | `2024-12-01-preview` | 必须是 API 支持的版本号 |

**快速验证脚本**：
```powershell
python -c "
from dotenv import load_dotenv; import os
load_dotenv()
print('ENDPOINT:', os.getenv('AZURE_OPENAI_ENDPOINT', '(未设置)'))
print('KEY:', os.getenv('AZURE_OPENAI_API_KEY', '(未设置)')[:8] + '...' if os.getenv('AZURE_OPENAI_API_KEY') else '(未设置)')
print('DEPLOYMENT:', os.getenv('AZURE_OPENAI_DEPLOYMENT', '(未设置)'))
print('API_VERSION:', os.getenv('AZURE_OPENAI_API_VERSION', '(未设置)'))
"
```

**代码硬编码检查**：
```powershell
# 搜索代码中是否有硬编码的 key
findstr /s /i "api-key\|api_key.*=" *.py
# 确保所有 key 都从 os.getenv() 读取
```

## 2. 常见报错与处置

### 401 / 403 Unauthorized / Forbidden

**原因**：API Key 错误、Endpoint 错误、资源权限不足

**排查步骤**：
1. 在 Azure Portal → 资源 → "密钥和终结点" 页面核对 Key 和 Endpoint
2. 确认 `.env` 中复制的 key 没有多余空格或换行
3. 确认 Subscription 已开通 Azure OpenAI 服务
4. 如果使用 RBAC，确认当前身份有 `Cognitive Services OpenAI User` 角色

### 404 / DeploymentNotFound

**原因**：`AZURE_OPENAI_DEPLOYMENT` 与 Azure Portal 的 deployment name 不一致

**排查步骤**：
1. Azure Portal → Azure OpenAI → "部署" → 查看部署名称
2. 确认 `.env` 中的 `AZURE_OPENAI_DEPLOYMENT` 值**完全一致**（区分大小写）
3. 如果从未创建部署，需先在 Portal 中创建

### 429 / RateLimit / Quota Exceeded

**原因**：请求频率或 token 配额超限

**处置**：
- **降低并发**：一次只跑一个请求，不要并行调用
- **降低 max_completion_tokens**：`02_analysis.py` 和 `03_stock_prediction.py` 默认使用 16384，可临时改为 8192
- **缩短 prompt**：减少传入的原始表格文本量（见下方"提示词压缩"）
- **加重试与退避**：在代码中添加指数退避

**添加重试的代码模板**：
```python
import time

def call_azure_with_retry(client, deployment, messages, max_retries=3, max_tokens=16384):
    """带退避重试的 Azure OpenAI 调用"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=messages,
                max_completion_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                print(f"[重试] 遇到限流，{wait}s 后重试 ({attempt+1}/{max_retries})...")
                time.sleep(wait)
                continue
            elif "timeout" in error_str.lower():
                # 超时：缩短 prompt 后重试
                print(f"[重试] 超时，尝试缩短内容后重试 ({attempt+1}/{max_retries})...")
                if attempt < max_retries - 1:
                    # 截断最后一条消息
                    messages[-1]["content"] = messages[-1]["content"][:len(messages[-1]["content"])//2]
                continue
            else:
                return f"API调用失败: {error_str}"
    return "API调用失败: 已达最大重试次数"
```

### 超时 / 长时间无输出

**原因**：Prompt 太长，模型响应时间超过客户端超时限制

**处置**：
1. **缩短 prompt**：只传摘要数据，不传原始表格
2. **先做本地摘要再问 LLM**：让 02_analysis.py 只分析 `summary + index + 结构统计`
3. **减少 `max_completion_tokens`**：从 16384 降到 8192
4. **检查网络**：确认能访问 Azure 端点
   ```powershell
   curl https://<resource>.cognitiveservices.azure.com/openai/models?api-version=2024-12-01-preview -H "api-key: YOUR_KEY"
   ```

### 空响应 / 截断 / 解析失败

**原因**：模型输出被截断，或返回了 Markdown 包裹的 JSON

**处置**：
1. 增加 `max_completion_tokens`
2. 在 system prompt 中强调"只输出纯 JSON，不要 Markdown"
3. 解析时尝试提取首个 `{...}` 块再 parse
4. 完整方案见 `llm-json-and-prompt-compression` skill

## 3. 质量/稳定性优化策略

### 02_analysis.py 优化
- 只传 `summary + index + 少量结构统计`（涨跌幅分布、成交额集中度等）
- 不传完整 daily 表（5000+ 行太长）

### 03_stock_prediction.py 优化
- 板块/个股结果先本地评分（`03_stock_prediction.py` 的综合得分）
- LLM 只负责"解释与建议"，不负责计算
- prompt 中只传 Top-5 板块 + 每板块 Top-5 股票（25 只即可）

### 通用优化
- 对 `client.chat.completions.create()` 始终包 try/except
- 超时设为 60-120 秒（openai 库默认较短）
- 打印 API 响应长度以便诊断截断问题

## 4. 连通性快速测试

```powershell
python -c "
from dotenv import load_dotenv; import os
load_dotenv()
from openai import AzureOpenAI

client = AzureOpenAI(
    api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
)
try:
    resp = client.chat.completions.create(
        model=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-5'),
        messages=[{'role': 'user', 'content': '回复OK'}],
        max_completion_tokens=10,
    )
    print('连通测试通过:', resp.choices[0].message.content)
except Exception as e:
    print('连通测试失败:', e)
"
```
