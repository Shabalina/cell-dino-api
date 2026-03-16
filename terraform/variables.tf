variable "env" {
  type        = string
  description = "The environment name (prod or qa)"
}
variable "region" {
  type        = string
  description = "AWS region"
}

variable "commit_sha" {
  type = string
}

variable "image_tag" {
  type        = string
  description = "latest"
}

variable "ecr_url" {
  type        = string
  description = "The full URL of the ECR repository"
}

variable "sagemaker_role_arn" {
  type        = string
  description = "The ARN of the IAM role SageMaker uses to run the container"
}