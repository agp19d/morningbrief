# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Serverless pipeline that delivers a daily AI & tech news email. An EventBridge cron triggers an AWS Lambda that searches the web via Tavily, synthesizes results with an LLM via LiteLLM, renders HTML/plain-text emails with Jinja2, and sends via Gmail SMTP.

## Build & Deploy

```bash
# Build Lambda deployment package (requires uv on PATH)
python scripts/build_lambda.py    # outputs lambda.zip at project root

# Terraform (dev)
cd terraform/environments/dev
terraform init
terraform plan
terraform apply

# Terraform (prod)
cd terraform/environments/prod
terraform init
terraform plan
terraform apply
```

The build script uses `uv pip install --python-platform linux` to get manylinux wheels for Lambda regardless of host OS. Always rebuild lambda.zip before `terraform apply`.

## Architecture

**Pipeline flow:** `lambda_function.py` (entry point) -> `fetcher.py` (Tavily search + LiteLLM completion) -> `renderer.py` (Jinja2 templates) -> `sender.py` (Gmail SMTP)

**Config resolution** (`config.py`): three-tier fallback — `config.ini` (local dev, git-ignored) > environment variables (Lambda/CI) > hard-coded defaults. Secrets must never be hard-coded; in prod they come from Lambda env vars injected by Terraform via `TF_VAR_*` from GitHub Secrets.

**LLM provider switching:** Change `LLM_MODEL` to any LiteLLM-compatible string (e.g. `openai/gpt-4o-mini`, `gemini/gemini-1.5-flash`). `config.py` auto-injects the API key into the correct provider env var.

**Terraform structure:** Reusable module at `terraform/modules/morning-brief/` consumed by two environment roots (`dev/`, `prod/`). Dev has `enable_schedule = false` (manual invocation only); prod has the EventBridge cron. Remote state in S3 with DynamoDB locking.

## Environment & Branching

- **`development` branch** -> deploys to dev (GitHub Actions: `deploy-dev.yml`)
- **`master` branch** -> deploys to prod (GitHub Actions: `deploy-prod.yml`)
- Dev Lambda has no schedule — invoke manually for testing
- Prod Lambda runs daily at 11:00 UTC (6:00 AM Panama time)

## Key Details

- Python 3.12, dependencies managed with `uv`, defined in `pyproject.toml`
- Lambda handler: `lambda_function.lambda_handler`
- System prompt lives at `src/prompts/system_prompt.txt` — uses `{topics}` and `{max_links}` placeholders
- Email templates: `src/templates/email.html` and `src/templates/email.txt`
- `config.ini` is git-ignored and contains secrets for local dev — never commit it
- No test suite currently exists
