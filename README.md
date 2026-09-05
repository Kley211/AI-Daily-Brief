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
ai-brief preview
ai-brief send
```

`preview` 会生成 `data/latest_digest.html` 和 `data/latest_digest.txt`；`send` 会在配置 SMTP 后发送日报；`run` 执行完整流水线但不发送邮件。

## 每日自动发送（Windows）

先确认手动 `send` 成功，再以管理员或当前用户运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register_daily_task.ps1 -Time "08:00"
```

任务会每天调用 `scripts/run_daily_brief.ps1`，运行日志写入 `data/daily_run.log`。取消任务：

```powershell
schtasks.exe /Delete /TN "AI Daily Brief" /F
```

## GitHub Actions 部署

GitHub Actions 不依赖本地电脑开机。将仓库推送到 GitHub 后，在仓库的 `Settings -> Secrets and variables -> Actions` 中新增以下 Repository secrets：

```text
AI_BRIEF_MODEL_API_KEY
AI_BRIEF_MODEL_NAME       （可选，默认 deepseek-chat）
AI_BRIEF_RECIPIENT
AI_BRIEF_SMTP_HOST
AI_BRIEF_SMTP_PORT        （可选，默认 587）
AI_BRIEF_SMTP_USERNAME
AI_BRIEF_SMTP_PASSWORD
AI_BRIEF_SMTP_FROM
```

工作流文件为 `.github/workflows/daily-brief.yml`，每天北京时间 08:00 自动运行，也可以在 GitHub Actions 页面点击 `Run workflow` 手动测试。GitHub 的定时任务可能有几分钟延迟。

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
