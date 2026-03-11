terraform {
  backend "s3" {
    bucket = "terraform-state-bucket-sha"
    key    = "sagemaker/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "random_id" "model_suffix" {
  byte_length = 4
  # This ensures the ID ONLY changes when the image tag changes
  keepers = {
    image_tag = var.image_tag
  }
}

# 1. Model
resource "aws_sagemaker_model" "cell_dino_model" {
  name               = "cell-dino-model-${random_id.model_suffix.hex}"
  execution_role_arn = var.sagemaker_role_arn

  primary_container {
    image = "${var.ecr_url}:${var.image_tag}"
  }
}

# 2. Endpoint Configuration (Serverless settings)
resource "aws_sagemaker_endpoint_configuration" "cell_dino_config" {
  name = "cell-dino-config-${random_id.model_suffix.hex}"

  production_variants {
    variant_name = "AllTraffic"
    model_name   = aws_sagemaker_model.cell_dino_model.name

    serverless_config {
      max_concurrency   = 5
      memory_size_in_mb = 3072
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# 3. The Endpoint (The permanent address)
resource "aws_sagemaker_endpoint" "cell_dino_endpoint" {
  name                 = "cell-dino-serverless-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.cell_dino_config.name

  lifecycle {
    ignore_changes = [tags]
  }
}