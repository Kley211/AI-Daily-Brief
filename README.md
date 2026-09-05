# AI Daily Brief

个人 AI 每日简报 MVP。当前实现 RoadMap 阶段 0：项目骨架、配置加载、日志和 CLI 入口。

## 环境

- Python 3.11+
- 建议使用虚拟环境

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

## CLI

```powershell
ai-brief run
ai-brief fetch
ai-brief process
ai-brief digest
```

阶段 0 中上述命令执行占位流程并输出结构化日志；来源抓取、AI 处理和邮件发送将在后续阶段实现。

## LLM 配置

默认使用离线规则处理；填写 API Key 后自动使用 DeepSeek。DeepSeek endpoint 已内置，不需要填写 URL：

```text
AI_BRIEF_MODEL_PROVIDER=deepseek
AI_BRIEF_MODEL_API_KEY=your-key
AI_BRIEF_MODEL_NAME=deepseek-chat
# AI_BRIEF_MODEL_ENDPOINT 留空，使用内置默认地址
```


## 测试

```powershell
pytest
```
