################################################################################
# modules/morning-brief/variables.tf
# Input variables for the reusable Morning Brief module.
# Consumed by terraform/environments/dev and terraform/environments/prod.
################################################################################

variable "environment" {
  description = "Deployment environment name (dev | prod). Used to suffix all resource names."
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be 'dev' or 'prod'."
  }
}

variable "enable_schedule" {
  description = "When true, creates an EventBridge cron rule to trigger the Lambda daily. Set to false for dev (manual invocation only)."
  type        = bool
}

variable "schedule_expression" {
  description = "EventBridge cron expression for the daily trigger. Only used when enable_schedule is true."
  type        = string
  default     = "cron(0 11 * * ? *)"  # 11:00 UTC = 6:00 AM Panama time
}

# ── Lambda ──────────────────────────────────────────────────────────────────

variable "lambda_zip_path" {
  description = "Path to the built Lambda deployment package (lambda.zip). Relative to the environment directory calling this module."
  type        = string
  default     = "../../../lambda.zip"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds."
  type        = number
  default     = 180
}

variable "lambda_memory_mb" {
  description = "Lambda function memory allocation in MB."
  type        = number
  default     = 256
}

# ── LLM ─────────────────────────────────────────────────────────────────────

variable "llm_model" {
  description = "LiteLLM model string (provider/model-name). Change to switch LLM providers without code changes."
  type        = string
  default     = "anthropic/claude-haiku-4-5-20251001"
}

variable "anthropic_api_key" {
  description = "API key for the configured LLM provider."
  type        = string
  sensitive   = true
}

# ── Tavily ───────────────────────────────────────────────────────────────────

variable "tavily_api_key" {
  description = "Tavily API key for web search."
  type        = string
  sensitive   = true
}

# ── Email (AWS SES) ─────────────────────────────────────────────────────────

variable "ses_from_email" {
  description = "Verified SES sender email address."
  type        = string
}

variable "ses_to_email" {
  description = "Recipient email address. Defaults to ses_from_email if empty."
  type        = string
  default     = ""
}

variable "ses_region" {
  description = "AWS region for SES. Defaults to us-east-1."
  type        = string
  default     = "us-east-1"
}
