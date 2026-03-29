################################################################################
# variables.tf
# Input variables for the AI Morning Brief infrastructure.
#
# In CI/CD (GitHub Actions), these are supplied via -var flags sourced from
# GitHub Actions secrets. Locally, pass them via terraform.tfvars (git-ignored)
# or export TF_VAR_<name> environment variables.
################################################################################

# ── AWS ────────────────────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region to deploy all resources into."
  type        = string
  default     = "us-east-1"
}

# ── Lambda ─────────────────────────────────────────────────────────────────

variable "lambda_zip_path" {
  description = "Path to the built Lambda deployment package (lambda.zip). Build it first with scripts/build_lambda.py."
  type        = string
  default     = "../lambda.zip"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds. The brief fetch can take up to 60s."
  type        = number
  default     = 180
}

variable "lambda_memory_mb" {
  description = "Lambda function memory allocation in MB."
  type        = number
  default     = 256
}

# ── Schedule ───────────────────────────────────────────────────────────────

variable "schedule_expression" {
  description = "EventBridge cron expression for the daily trigger. Default: 11:00 UTC = 6:00 AM Panama time."
  type        = string
  default     = "cron(0 11 * * ? *)"
}

# ── LLM (LiteLLM) ──────────────────────────────────────────────────────────

variable "llm_model" {
  description = "LiteLLM model string (provider/model-name). Change this to switch providers without any code change."
  type        = string
  default     = "anthropic/claude-haiku-4-5-20251001"
}

variable "anthropic_api_key" {
  description = "Anthropic API key. Used when llm_model is set to an anthropic/* model."
  type        = string
  sensitive   = true
}

# ── Tavily ─────────────────────────────────────────────────────────────────

variable "tavily_api_key" {
  description = "Tavily API key for web search. Get one at https://app.tavily.com."
  type        = string
  sensitive   = true
}

# ── Email ──────────────────────────────────────────────────────────────────

variable "gmail_address" {
  description = "Gmail address used to send the brief (the FROM address)."
  type        = string
}

variable "gmail_app_password" {
  description = "Gmail App Password (16 characters, no spaces). Not your regular Gmail password."
  type        = string
  sensitive   = true
}

variable "to_email" {
  description = "Recipient email address. Defaults to gmail_address (send to yourself) if left empty."
  type        = string
  default     = ""
}
