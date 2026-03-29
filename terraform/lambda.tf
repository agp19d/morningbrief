################################################################################
# lambda.tf
# Core infrastructure for the AI Morning Brief:
#   - IAM execution role
#   - Lambda function (with environment variables for all secrets)
#   - CloudWatch Log Group (explicit, with 14-day retention)
#   - EventBridge rule + target (daily cron trigger)
#   - Lambda permission (allows EventBridge to invoke the function)
################################################################################

# ── IAM role ───────────────────────────────────────────────────────────────

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
  name               = "morning-brief-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  description = "Execution role for the AI Morning Brief Lambda function."
}

# Grants permission to write logs to CloudWatch Logs.
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ── Lambda function ─────────────────────────────────────────────────────────
# Note: Lambda automatically creates /aws/lambda/ai-morning-brief in
# CloudWatch Logs on first invocation. No explicit resource needed.

resource "aws_lambda_function" "morning_brief" {
  function_name = "ai-morning-brief"
  description   = "Fetches today's AI & tech news and emails a morning brief."

  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  # Handler path matches the location of lambda_handler inside the zip.
  # src/ contents are zipped as the root, so the module is lambda_function.
  handler = "lambda_function.lambda_handler"
  runtime = "python3.12"

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_mb

  role = aws_iam_role.lambda_exec.arn

  # All secrets are injected as environment variables.
  # config.py reads these automatically — no code changes needed.
  environment {
    variables = {
      LLM_MODEL          = var.llm_model
      ANTHROPIC_API_KEY  = var.anthropic_api_key
      TAVILY_API_KEY     = var.tavily_api_key
      GMAIL_ADDRESS      = var.gmail_address
      GMAIL_APP_PASSWORD = var.gmail_app_password
      TO_EMAIL           = coalesce(var.to_email, var.gmail_address)
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
  ]
}

# ── EventBridge (CloudWatch Events) schedule ───────────────────────────────

resource "aws_cloudwatch_event_rule" "daily_schedule" {
  name                = "morning-brief-daily"
  description         = "Triggers the AI Morning Brief Lambda on a daily schedule."
  schedule_expression = var.schedule_expression
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "morning_brief" {
  rule      = aws_cloudwatch_event_rule.daily_schedule.name
  target_id = "MorningBriefLambda"
  arn       = aws_lambda_function.morning_brief.arn
}

# Allow EventBridge to invoke the Lambda function.
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.morning_brief.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_schedule.arn
}
