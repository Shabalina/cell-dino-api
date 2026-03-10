# The Role
resource "aws_iam_role" "apigw_sagemaker_role" {
  name = "apigw-sagemaker-invocation-role"

  # Allows the API Gateway service to assume the role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

# 2. The Permission Policy
resource "aws_iam_role_policy" "apigw_sagemaker_policy" {
  name = "apigw-sagemaker-invocation-policy"
  role = aws_iam_role.apigw_sagemaker_role.id

  # Allows the role to call sagemaker endpoint
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "sagemaker:InvokeEndpoint"
        Effect   = "Allow"
        Resource = aws_sagemaker_endpoint.cell_dino_endpoint.arn
      }
    ]
  })
}