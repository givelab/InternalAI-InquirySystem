terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # リモートステート管理を使う場合はここで backend を設定する（任意）
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "internal-ai/terraform.tfstate"
  #   region = "ap-northeast-1"
  # }
}

provider "aws" {
  region = var.aws_region

  # すべてのリソースに共通タグを付与
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
