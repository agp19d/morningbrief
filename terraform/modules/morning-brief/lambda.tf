################################################################################
# modules/morning-brief/lambda.tf
# Core AWS infrastructure for the Morning Brief.
# All resource names are suffixed with var.environment (dev | prod).
#
# EventBridge schedule resources are conditional:
#   enable_schedule = true  → daily cron trigger (prod)
#   enable_schedule = false → no schedule, manual invocation only (dev)
################################################################################

# ── IAM role ────────────────────────────────────────────────────────────────

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "morning-brief-lambda-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  description        = "Execution role for the AI Morning Brief Lambda (${var.environment})."
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ── Lambda function ──────────────────────────────────────────────────────────

resource "aws_lambda_function" "morning_brief" {
  function_name = "ai-morning-brief-${var.environment}"
  description   = "AI Morning Brief — ${var.environment} environment."

  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  handler = "lambda_function.lambda_handler"
  runtime = "python3.12"

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_mb

  role = aws_iam_role.lambda_exec.arn

  environment {
    variables = {
      LLM_MODEL          = var.llm_model
      ANTHROPIC_API_KEY  = var.anthropic_api_key
      TAVILY_API_KEY     = var.tavily_api_key
      GMAIL_ADDRESS      = var.gmail_address
      GMAIL_APP_PASSWORD = var.gmail_app_password
      TO_EMAIL           = coalesce(var.to_email, var.gmail_address)
      ENVIRONMENT        = var.environment
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_basic_execution]
}

# ── EventBridge schedule (prod only) ────────────────────────────────────────
# count = 0 in dev → no scheduled trigger, Lambda is invoked manually only.

resource "aws_cloudwatch_event_rule" "daily_schedule" {
  count = var.enable_schedule ? 1 : 0

  name                = "morning-brief-daily-${var.environment}"
  description         = "Triggers the AI Morning Brief Lambda daily (${var.environment})."
  schedule_expression = var.schedule_expression
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "morning_brief" {
  count = var.enable_schedule ? 1 : 0

  rule      = aws_cloudwatch_event_rule.daily_schedule[0].name
  target_id = "MorningBriefLambda-${var.environment}"
  arn       = aws_lambda_function.morning_brief.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  count = var.enable_schedule ? 1 : 0

  statement_id  = "AllowEventBridgeInvoke-${var.environment}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.morning_brief.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_schedule[0].arn
}
