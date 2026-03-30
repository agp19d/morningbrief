################################################################################
# environments/dev/main.tf
# Development environment — manual invocation only, no schedule.
#
# Trigger: GitHub Actions on push to the `development` branch.
# State:   s3://morningbrief-terraform-state/morning-brief/dev/terraform.tfstate
################################################################################

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "morningbrief-terraform-state"
    key            = "morning-brief/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "morning-brief-tf-locks"
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "morning-brief"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

module "morning_brief" {
  source = "../../modules/morning-brief"

  environment     = "dev"
  enable_schedule = false   # Dev Lambda is invoked manually only

  lambda_zip_path = "../../../lambda.zip"

  llm_model          = var.llm_model
  anthropic_api_key  = var.anthropic_api_key
  tavily_api_key     = var.tavily_api_key
  gmail_address      = var.gmail_address
  gmail_app_password = var.gmail_app_password
  to_email           = var.to_email
}

# ── Outputs ──────────────────────────────────────────────────────────────────

output "lambda_function_name" { value = module.morning_brief.lambda_function_name }
output "lambda_function_arn"  { value = module.morning_brief.lambda_function_arn }
output "cloudwatch_log_group" { value = module.morning_brief.cloudwatch_log_group }

# ── Variables (supplied via TF_VAR_* env vars in CI) ─────────────────────────

variable "llm_model"          { default   = "anthropic/claude-haiku-4-5-20251001" }
variable "anthropic_api_key"  { sensitive = true }
variable "tavily_api_key"     { sensitive = true }
variable "gmail_address"      {}
variable "gmail_app_password" { sensitive = true }
variable "to_email"           { default   = "" }
