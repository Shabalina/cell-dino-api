# Archive provider to zip the Python file
data "archive_file" "lambda_zip" {
  count       = terraform.workspace == "prod" ? 1 : 0
  type        = "zip"
  source_file = "${path.module}/../src/monitoring/heartbeat.py"
  output_path = "${path.module}/heartbeat_payload.zip"
}

# Lambda Function
resource "aws_lambda_function" "heartbeat_lambda" {
  count = terraform.workspace == "prod" ? 1 : 0

  filename         = data.archive_file.lambda_zip[0].output_path
  source_code_hash = data.archive_file.lambda_zip[0].output_base64sha256 # Trigger redeploy on code change

  function_name = "streamlit-heartbeat"
  role          = aws_iam_role.lambda_exec_role[0].arn
  handler       = "heartbeat.lambda_handler"
  runtime       = "python3.11"

  depends_on = [data.archive_file.lambda_zip]

  environment {
    variables = {
      STREAMLIT_URL = local.streamlit_url
    }
  }
}

# Execution Role for the Heartbeat Lambda
resource "aws_iam_role" "lambda_exec_role" {
  count = terraform.workspace == "prod" ? 1 : 0

  name = "heartbeat-lambda-role"

  # Policy allows the Lambda service to use this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Managed Policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  count = terraform.workspace == "prod" ? 1 : 0

  role       = aws_iam_role.lambda_exec_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda as the Target for the Rule
resource "aws_cloudwatch_event_target" "trigger_heartbeat_lambda" {
  count = terraform.workspace == "prod" ? 1 : 0

  rule      = aws_cloudwatch_event_rule.streamlit_heartbeat_schedule[0].name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.heartbeat_lambda[0].arn
}

# CloudWatch Event Rule (The Cron Schedule)
resource "aws_cloudwatch_event_rule" "streamlit_heartbeat_schedule" {
  count = terraform.workspace == "prod" ? 1 : 0

  name                = "streamlit-heartbeat-schedule"
  description         = "Triggers Lambda every 12 hours to keep Streamlit app awake"
  schedule_expression = "rate(12 hours)"
}

# CloudWatch Permission to Invoke Lambda
resource "aws_lambda_permission" "allow_cloudwatch_to_call_heartbeat" {
  count = terraform.workspace == "prod" ? 1 : 0

  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.heartbeat_lambda[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.streamlit_heartbeat_schedule[0].arn
}

