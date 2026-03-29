################################################################################
# outputs.tf
# Useful values printed after terraform apply.
################################################################################

output "lambda_function_name" {
  description = "Name of the deployed Lambda function."
  value       = aws_lambda_function.morning_brief.function_name
}

output "lambda_function_arn" {
  description = "ARN of the deployed Lambda function."
  value       = aws_lambda_function.morning_brief.arn
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule that triggers the daily brief."
  value       = aws_cloudwatch_event_rule.daily_schedule.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group name for Lambda logs."
  value       = "/aws/lambda/ai-morning-brief"
}
