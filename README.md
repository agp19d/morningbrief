# AI Morning Brief

A serverless pipeline that delivers a daily AI & tech news email every morning at 6:00 AM Panama time.

Each morning it searches the web for fresh news across configured topics, synthesizes the results into a structured brief using a large language model, and sends a styled HTML email to your inbox — fully automated, zero manual steps.

---

## How it works

```
EventBridge (cron)
      │
      ▼
 Lambda Function
      │
      ├── Tavily API ──► web search (one query per topic)
      │                       │
      │                  search results
      │                       │
      ├── LiteLLM ────────────┘
      │   (Anthropic / OpenAI / Gemini)
      │        │
      │    structured JSON brief
      │        │
      └── Gmail SMTP ──► email delivered
```

1. **EventBridge** triggers the Lambda function on a daily cron schedule.
2. **Tavily** runs one web search per configured topic to gather fresh articles.
3. **LiteLLM** passes the search results to the configured LLM, which returns a structured JSON brief (headline, bullets, sources, deep dive).
4. The brief is rendered into HTML via **Jinja2 templates** and sent via **Gmail SMTP**.

### Switching LLM providers

Change a single config value — no code changes needed:

```
LLM_MODEL = "openai/gpt-4o-mini"       # OpenAI
LLM_MODEL = "gemini/gemini-1.5-flash"  # Google
LLM_MODEL = "anthropic/claude-haiku-4-5-20251001"  # Anthropic (default)
```

---

## Project structure

```
src/
├── lambda_function.py   # Entry point — wires fetch → render → send
├── config.py            # Config loader (config.ini → env vars → defaults)
├── fetcher.py           # Tavily search + LiteLLM completion
├── renderer.py          # Jinja2 template rendering
├── sender.py            # Gmail SMTP sending
├── prompts/
│   └── system_prompt.txt
└── templates/
    ├── email.html
    └── email.txt

terraform/               # Infrastructure as code (AWS)
scripts/
└── build_lambda.py      # Packages src/ + deps into lambda.zip
```

---

## Infrastructure

Managed with Terraform. Remote state is stored in S3 with DynamoDB locking.

| Resource | Name | Purpose |
|---|---|---|
| `aws_lambda_function` | `ai-morning-brief` | Runs the brief pipeline |
| `aws_iam_role` | `morning-brief-lambda-role` | Lambda execution role |
| `aws_cloudwatch_event_rule` | `morning-brief-daily` | Daily cron trigger (11:00 UTC) |
| `aws_cloudwatch_event_target` | `MorningBriefLambda` | Connects EventBridge to Lambda |
| `aws_lambda_permission` | `AllowEventBridgeInvoke` | Grants EventBridge invoke access |
| `aws_s3_bucket` | `morningbrief-terraform-state` | Terraform remote state |
| `aws_dynamodb_table` | `morning-brief-tf-locks` | Terraform state locking |
