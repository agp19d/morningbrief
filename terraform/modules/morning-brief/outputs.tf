################################################################################
# modules/morning-brief/outputs.tf
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
  description = "ARN of the EventBridge schedule rule. Empty string when enable_schedule is false."
  value       = var.enable_schedule ? aws_cloudwatch_event_rule.daily_schedule[0].arn : ""
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group name for Lambda logs."
  value       = "/aws/lambda/${aws_lambda_function.morning_brief.function_name}"
}
