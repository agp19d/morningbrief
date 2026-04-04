# AI Morning Brief

A serverless pipeline that delivers a daily AI & tech news email every morning at 6:00 AM Panama time (11:00 UTC).

Each morning it searches the web for fresh news across configured topics, synthesizes the results into a structured brief using a large language model, and sends a styled HTML email to your inbox — fully automated, zero manual steps.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Infrastructure](#infrastructure)
- [Switching LLM Providers](#switching-llm-providers)
- [Contributing](#contributing)

---

## How It Works

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
      ├── Jinja2 ──► HTML + plain-text rendering
      │        │
      └── Gmail SMTP ──► email delivered
```

1. **EventBridge** triggers the Lambda function on a daily cron schedule.
2. **Tavily** runs one web search per configured topic to gather fresh articles.
3. **LiteLLM** passes the search results to the configured LLM, which returns a structured JSON brief (headline, bullets, sources, deep dive).
4. **Jinja2** renders the brief into HTML and plain-text email templates.
5. **Gmail SMTP** delivers the multipart email to the configured recipient.

---

## Project Structure

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
    ├── email.html       # HTML email template (dark theme)
    └── email.txt        # Plain-text fallback

tests/
├── conftest.py          # Shared fixtures (sample_brief, tavily_results)
├── test_config.py       # Config loading and validation tests
├── test_fetcher.py      # Search + LLM response tests
├── test_renderer.py     # Template rendering tests
├── test_sender.py       # SMTP sending tests
└── test_lambda_function.py  # End-to-end handler tests

terraform/
├── modules/morning-brief/   # Reusable Terraform module
│   ├── lambda.tf
│   ├── variables.tf
│   └── outputs.tf
└── environments/
    ├── dev/main.tf          # Dev — manual invocation only
    └── prod/main.tf         # Prod — daily EventBridge cron

scripts/
└── build_lambda.py      # Packages src/ + deps into lambda.zip

.github/workflows/
├── deploy-dev.yml       # CI/CD for development branch
└── deploy-prod.yml      # CI/CD for master branch
```

---

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **Terraform >= 1.6** — infrastructure provisioning
- **AWS CLI** — configured with appropriate credentials
- **Gmail App Password** — [generate one here](https://myaccount.google.com/apppasswords)

---

## Local Development

### 1. Clone and set up

```bash
git clone https://github.com/agp19d/morning-brief.git
cd morning-brief
uv venv
uv pip install -e ".[dev]"
```

### 2. Configure secrets

Copy the example below into `config.ini` at the project root (this file is git-ignored):

```ini
[llm]
model = anthropic/claude-haiku-4-5-20251001
api_key = sk-ant-...

[tavily]
api_key = tvly-...

[email]
gmail_address = you@gmail.com
gmail_app_password = xxxx xxxx xxxx xxxx
to_email = recipient@example.com

[brief]
max_source_links = 2
topics = AI Models & Research, Big Tech, Agentic AI

[schedule]
delivery_label = 6:00 AM
```

### 3. Run locally

```bash
cd src
python -c "from lambda_function import lambda_handler; lambda_handler({}, None)"
```

---

## Configuration

Configuration follows a three-tier fallback (highest priority first):

| Priority | Source | Use Case |
|----------|--------|----------|
| 1 | `config.ini` | Local development |
| 2 | Environment variables | Lambda / CI |
| 3 | Hard-coded defaults | Non-secret settings |

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_MODEL` | LiteLLM model string | No (default: `anthropic/claude-haiku-4-5-20251001`) |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes (if using Anthropic) |
| `TAVILY_API_KEY` | Tavily web search key | Yes |
| `GMAIL_ADDRESS` | Sender Gmail address | Yes |
| `GMAIL_APP_PASSWORD` | Gmail App Password | Yes |
| `TO_EMAIL` | Recipient email | No (defaults to `GMAIL_ADDRESS`) |

---

## Running Tests

```bash
# Run all tests
uv run pytest

# With verbose output
uv run pytest -v

# With coverage report
uv run pytest --cov=src --cov-report=term-missing
```

All external services (Tavily, LiteLLM, Gmail SMTP) are mocked in tests.

---

## Deployment

### Build the Lambda package

```bash
python scripts/build_lambda.py    # outputs lambda.zip at project root
```

The build script uses `uv pip install --python-platform linux` to get manylinux wheels regardless of host OS.

### Deploy with Terraform

```bash
# Dev environment
cd terraform/environments/dev
terraform init
terraform plan
terraform apply

# Prod environment
cd terraform/environments/prod
terraform init
terraform plan
terraform apply
```

### CI/CD (GitHub Actions)

| Branch | Workflow | Environment |
|--------|----------|-------------|
| `development` | `deploy-dev.yml` | Dev (no schedule) |
| `master` | `deploy-prod.yml` | Prod (daily cron) |

Secrets are injected as `TF_VAR_*` environment variables from GitHub Secrets.

---

## Infrastructure

Managed with Terraform. Remote state stored in S3 with DynamoDB locking.

| Resource | Name | Purpose |
|----------|------|---------|
| Lambda Function | `ai-morning-brief-{env}` | Runs the brief pipeline |
| IAM Role | `morning-brief-lambda-role-{env}` | Lambda execution role |
| EventBridge Rule | `morning-brief-daily-{env}` | Daily cron trigger (prod only) |
| S3 Bucket | `morningbrief-terraform-state` | Terraform remote state |
| DynamoDB Table | `morning-brief-tf-locks` | Terraform state locking |

---

## Switching LLM Providers

Change a single config value — no code changes needed:

```ini
# config.ini (local) or LLM_MODEL env var (Lambda)
model = openai/gpt-4o-mini          # OpenAI
model = gemini/gemini-1.5-flash     # Google
model = anthropic/claude-haiku-4-5-20251001  # Anthropic (default)
```

Set the corresponding API key (`OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.) and LiteLLM handles the rest.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards, naming conventions, and contribution guidelines.

---

## License

MIT
