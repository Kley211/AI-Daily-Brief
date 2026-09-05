# AI Daily Brief MVP

## 1. 文档信息

- 文档：Architecture Requirements Document
- 版本：v0.1
- 状态：Draft
- 适用范围：个人使用的每日 AI 情报邮件 MVP

## 2. 架构原则

- 先保证信息质量和可追溯性，再扩大来源数量。
- RSS/API 优先，公开页面抓取作为兜底。
- 每个来源独立适配，单源故障不能拖垮全局。
- 原始内容与模型生成内容分离保存。
- 所有摘要和判断都必须能回链到原始来源。
- MVP 采用单体应用加定时任务，保留后续拆分边界。

## 3. 总体架构

```text
Scheduler
   |
   v
Source Adapters --> Raw Items --> Normalizer --> Deduplicator
                                             |
                                             v
                                      Event Clustering
                                             |
                                             v
                               LLM Enrichment / Scoring
                                             |
                                             v
                                      Digest Renderer
                                             |
                                             v
                                       Email Sender
```

建议技术栈：Python、FastAPI（可选管理接口）、SQLite 起步、PostgreSQL 可替换、APScheduler 或 GitHub Actions 定时、Jinja2 邮件模板、SMTP 或 Resend 邮件服务。

## 4. 组件要求

### 4.1 Scheduler

- 默认每天 08:00（Asia/Shanghai）生成并发送日报。
- 支持手工触发一次运行。
- 记录任务开始、结束、耗时和最终状态。
- 支持失败重试，避免重复发送需使用日报日期和运行批次幂等键。

### 4.2 Source Adapters

每个适配器统一输出：

```text
source_id
external_id
title
url
author
published_at
content_excerpt
metadata
```

适配器实现建议：

- OpenAI、Anthropic、Hugging Face、LangChain、LlamaIndex：RSS 或公开页面。
- Reddit：官方 RSS/API，保存帖子标题、正文摘要、评分、评论数和发布时间。
- Hacker News：使用 HN API 获取候选内容，再按 AI 关键词、标题和正文摘要过滤。

每个适配器都应有独立超时、重试和限流配置。

### 4.3 Normalizer

- 规范化 URL，移除追踪参数。
- 清理 HTML、脚本、导航和重复段落。
- 统一时区为 UTC 存储，在邮件中转换为 Asia/Shanghai。
- 生成内容哈希，避免同一内容重复入库。
- 保留原始抓取时间和原始响应元数据。

### 4.4 Deduplicator 与 Event Clustering

去重分三层：

1. URL 规范化去重。
2. 标题相似度去重。
3. 标题、摘要、实体和时间窗口结合的事件聚类。

聚类结果保留一个主事件和多个支持来源。不得因为标题不同就把同一事件拆成多条，也不得仅因关键词相同就错误合并无关事件。

### 4.5 LLM Enrichment

模型输出必须使用结构化 JSON，至少包含：

```json
{
  "category": "models|products|opensource|infra|research|policy|community",
  "summary": "...",
  "why_it_matters": "...",
  "importance": "high|medium|low",
  "confidence": "official|multi_source|single_source|community|unconfirmed",
  "entities": ["..."],
  "claims": ["..."],
  "needs_review": false
}
```

要求：

- 模型只能基于抓取内容生成结论。
- 无法从来源确认的内容必须降级为推测或待确认。
- JSON 解析失败时重试一次，仍失败则保留原始条目并标记处理失败。
- 高重要性或低置信度内容可标记 `needs_review`，由发送策略决定是否纳入重点区。

### 4.6 Ranking

默认排序可采用以下因素：

- 来源可靠度
- 与用户关注主题的相关性
- 事件新颖度
- 潜在影响力
- 社区传播速度

官方来源可靠度最高；Reddit 和 Hacker News 的热度主要影响“社区信号”排序，不应直接提升为官方重点消息。

### 4.7 Digest Renderer

- 使用 Jinja2 生成响应式 HTML 邮件。
- 同时生成纯文本版本，确保邮件客户端兼容。
- 邮件包含摘要、状态、来源、时间和原始链接。
- 无条目时生成正常的空日报，不发送空白邮件。
- 模板版本写入运行记录，便于回溯。

### 4.8 Email Sender

- 支持 SMTP 或邮件 API 二选一。
- 配置项通过环境变量注入，不写入仓库。
- 发送结果记录 message id、时间和错误信息。
- 发送失败时重试，并避免重复发送同一日报。

## 5. 数据模型

### `raw_items`

- `id`
- `source_id`
- `external_id`
- `title`
- `url`
- `published_at`
- `fetched_at`
- `content_excerpt`
- `content_hash`
- `metadata_json`

### `events`

- `id`
- `canonical_title`
- `first_seen_at`
- `last_seen_at`
- `category`
- `importance`
- `confidence`
- `summary`
- `why_it_matters`
- `entities_json`
- `needs_review`

### `event_sources`

- `event_id`
- `raw_item_id`
- `is_primary`

### `digests`

- `digest_date`
- `generated_at`
- `sent_at`
- `status`
- `item_count`
- `template_version`
- `error_message`

## 6. 配置要求

```yaml
timezone: Asia/Shanghai
send_time: "08:00"
lookback_hours: 24
max_digest_items: 10
recipient: ${DIGEST_RECIPIENT}
ai_keywords:
  - LLM
  - GPT
  - Claude
  - Gemini
  - agent
  - RAG
  - inference
  - GPU
```

密钥、邮箱密码和模型 API Key 只允许通过环境变量或本地密钥存储提供。

## 7. 失败处理与可观测性

- 单个来源失败：记录错误，继续处理其他来源。
- 模型失败：使用重试和降级模板；不得丢弃原始链接。
- 邮件失败：重试并保留未发送日报，支持手工补发。
- 每次运行输出结构化日志：`run_id`、来源、阶段、耗时、数量、错误。
- 记录抓取数量、去重数量、聚类数量、模型失败数和发送状态。

## 8. 安全与合规

- 遵守各站点公开访问规则、robots 和服务条款。
- 控制请求频率，设置合理 User-Agent。
- 不绕过登录、验证码、付费墙或访问控制。
- 只保存满足摘要和追溯所需的最小内容。
- 邮件中展示原文链接和来源，不复制完整文章。
- 对社区内容明确标注其非官方性质。

## 9. 部署方案

### MVP 推荐

- 一个 Python 项目。
- SQLite 数据库。
- 本地任务计划程序或 GitHub Actions 每日触发。
- SMTP/Resend 发送邮件。
- `.env` 保存本地配置，`.env.example` 提供字段说明。

### 后续升级

- SQLite 替换为 PostgreSQL。
- APScheduler 替换为 Celery/Temporal。
- 增加管理 API、历史归档和反馈接口。
- 将来源抓取、模型处理和邮件发送拆为独立 worker。

## 10. 验证要求

- 为每个来源编写最小解析测试样例。
- 使用固定样本验证 URL 去重和事件聚类。
- 对模型 JSON 输出做 schema 校验。
- 测试无新内容、单源失败、模型失败、邮件失败和重复运行场景。
- 连续运行 7 天后人工抽检摘要事实性、重复率和阅读体验。
