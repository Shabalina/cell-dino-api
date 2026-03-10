variable "region" {
  type        = string
  description = "AWS region"
}

variable "image_tag" {
  type        = string
  description = "The unique Docker image tag (for this project the git commit SHA)"
}

variable "ecr_url" {
  type        = string
  description = "The full URL of the ECR repository"
}

variable "sagemaker_role_arn" {
  type        = string
  description = "The ARN of the IAM role SageMaker uses to run the container"
}